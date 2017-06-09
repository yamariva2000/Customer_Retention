import re
from dateutil.relativedelta import relativedelta
from datetime import date

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import requests
import os


def generate_data(n_sample=100,periods=18):
    """generates random customer retention data using company names from the sec website"""
    np.random.seed(1)
    #save file name
    companies='companies.html'
    #download if file doesn't exit yet
    if not os.path.exists(companies):
        with open(companies,'w') as file:
            file.write(requests.get('https://www.sec.gov/rules/other/4-460list.htm').text)
    text=open(companies,'r').read()
    #get list of companies from the html file
    company_list=[i.strip('\n') for i in re.findall(r'<TD>([\s\w]+)',text) if len(i)>1]
    #list of industries, sales reps, possible MRR amounts
    industries=['Aviation','Automotive','Energy','Computer','Consumer Products']
    sales_rep=['Joe','Tim','Betty','Carol','Ann']
    mrr=[1000,2000,3000,4000,5000,10000]
    #total time period in months to generate
    length=60
    months=np.array(range(length))
    #starting date
    st_date=date(2014,1,1)

    no_companies=len(company_list)
    #generate random data
    indust_random=np.random.choice(industries,size=no_companies)
    rep_random=np.random.choice(sales_rep,size=no_companies)
    mrr_random=np.random.choice(mrr,size=no_companies)
    #random start months
    start=np.random.choice(months,size=no_companies)
    #start date for each company
    st_dates=[st_date+relativedelta(months=i) for i in start]
    #random sales term
    terms=np.around(np.random.normal(size=no_companies))*5+10
    terms=np.asarray(terms,dtype=int)
    #avoid negative terms
    terms[terms<0]=0

    total_mrr_act=terms*mrr_random
    total_mrr_con=length*mrr_random
    #dataframe of all companies
    universe=pd.DataFrame.from_dict({'Company':company_list,'Industry':indust_random,'Representative':rep_random,'mrr':mrr_random,'term':terms,'start date':st_dates,'total_mrr_act':total_mrr_act,'total_mrr_con':total_mrr_con})

    #get sample of the companies
    sample=universe.sample(n=n_sample)
    #reset indices
    sample.reset_index(inplace=True,drop=True)

    #another data frame to store monthly data
    mrr=pd.DataFrame({'id':[],'dates':[],'mrr_con':[],'mrr_act':[],'months':[]})
    for index,row in sample.iterrows():
        ids=np.array([index]*length)
        dates =np.array([row['start date']+relativedelta(months=i) for i in range(length)])
        mrr_con=np.array([row['mrr']]*length)
        mrr_act=np.array([row['mrr']]*row['term']+[0]*(length-row['term']))
        months=range(length)
        mrr_add=pd.DataFrame.from_dict({'id':ids,'dates':dates,'mrr_con':mrr_con,'mrr_act':mrr_act,'months':months})

        mrr=pd.concat([mrr,mrr_add])
        mrr.months=mrr.months.astype(int)
    #combine company and monthly data
    combo=pd.merge(sample,mrr,left_index=True,right_on='id')
    end_date = combo.dates.min() + relativedelta(months=periods)
    import datetime
    combo['Date'] = combo['start date'].apply(lambda x: x.strftime('%y-%m'))

    newcombo = combo[(combo['dates'] <= end_date)]
    return newcombo


def pivot_tables(combo=generate_data(),index=['Date']):
    pivot_act = pd.pivot_table(dropna=True, data=combo, values='mrr_act', index=index, columns='months',
                               aggfunc='sum', margins=True)
    pivot_ct = pd.pivot_table(dropna=True, data=combo, values='mrr_con', index=index, columns='months',
                              aggfunc='sum', margins=True)

    percent = pivot_act / pivot_ct

    return percent,pivot_act,pivot_ct


def plot(pivot_tables):
    percent, pivot_act, pivot_ct = pivot_tables

    sns.set(style="dark")
    # Set up the matplotlib figure
    f= plt.figure(figsize=(24, 18))

    # Generate a custom diverging colormap
    cmap = sns.diverging_palette(15, 150,as_cmap=True)


    ax=f.add_subplot(1,1,1)

    sns.heatmap(percent,cmap=cmap,ax=ax,annot=True,fmt='.0%',mask=None,cbar_kws={"orientation": "horizontal"})
    cbar = ax.collections[0].colorbar
    cbar.set_ticks([0, .25,.50, .75, 1])
    cbar.set_ticklabels(['0%', '25%','50%', '75%', '100%'])

    ax.set_yticklabels(ax.get_yticklabels(),rotation=0)

    inc=1/len(ax.get_yticklabels())
    st=0
    shift=1.1

    for i,j,k in zip(pivot_act.sum(axis=1),pivot_ct.sum(axis=1),ax.get_yticklabels()):
        ax.annotate('{:,.0f}/{:,.0f} ({:.0%})'.format(i/1000,j/1000,i/j), xy=(shift, 1-st), xycoords='axes fraction',
                    xytext=(shift, 1-st), textcoords='axes fraction',

                    horizontalalignment='right', verticalalignment='top',fontsize=11)
        st+=inc

    ax.annotate('MRR/Contract MRR',xytext=(shift-.1,1.05),xy=(shift,1.1),textcoords='axes fraction')
    title='Retention by {}'.format(','.join(percent.index.names))
    ax.set_title(title,fontsize=26,y=1.1)
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position('top')

    plt.savefig(title)

if __name__ =='__main__':

    plot(pivot_tables())



    plt.show()