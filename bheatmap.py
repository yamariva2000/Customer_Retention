from bokeh.charts import HeatMap, output_file, show
from bokeh.models import Range1d,FuncTickFormatter, FixedTicker,LabelSet,ColumnDataSource,LinearAxis
import numpy as np
from bokeh.charts import defaults
from bokeh.palettes import brewer
from conv import pivot_tables,generate_data
import pandas as pd
defaults.width = 1000
defaults.height = 700

def bokeh_heatmap(index=['Date','Representative']):
    #return three retention matrices
    percent_MRR,actual_MRR,contract_MRR=pivot_tables(combo=generate_data(n_sample=100,periods=30),index=index)

    #reformat data to column sparse matrix and place into dictionary
    x=[]
    y=[]
    vals=[]
    [(y.append(i[0]),x.append(i[1]),vals.append(v)) for i,v in np.ndenumerate(percent_MRR)
     ]
    data={'x':x,'y':y,'vals':vals}

    #heatmap instantiate
    hm=HeatMap(data=data,x='x',y='y',values='vals',stat=None,
               title='Revenue Retention by {}'.format(','.join(index)),ygrid=True,xgrid=True
               ,xlabel='months',ylabel='contract start', yscale='categorical',palette=brewer['RdYlGn'][11],
               title_text_font_size='20pt'
               )
    #add value labels to heat map
    # create formatted column of values for annotation labels
    data['labels']=['{:.0%}'.format(round(i,2)) if i>=0  else '' for i in data['vals']]
    #dropping vals which are not json compliant
    del data['vals']
    source=ColumnDataSource(data=data)
    labels = LabelSet(x='x', y='y', text='labels',level='glyph',
                      x_offset=-2, y_offset=-4, source=source, render_mode='canvas',text_font_size='7pt',text_color='white')
    hm.add_layout(labels)

    # customize y-axis text

    # new_index=actual_MRR.sum(axis=1).reset_index()
    # new_index.rename(columns={0: 'Actual MRR'}, inplace=True)
    # new_index['Contract MRR']=contract_MRR.sum(axis=1).reset_index()[0]
    y_label_dict={}


    for index,groups in enumerate(list(percent_MRR.index)):
        y_label_dict[index]='-'.join(groups)
    #reverse y-axis order
    hm.y_range.start=max(y_label_dict.keys())
    hm.y_range.end=min(y_label_dict.keys())
    hm.x_range=Range1d(0,12)
    #generate javascript code to reformat y-axis
    hm.yaxis.formatter=FuncTickFormatter(code="""var labels = {};
                                                 return labels[tick];
                                                 """.format(y_label_dict))
    # fix ticks to display all values
    hm.yaxis[0].ticker=FixedTicker(ticks=list(y_label_dict.keys()))


    total_contract_mrr=contract_MRR.sum(axis=1)
    total_actual_mrr=actual_MRR.sum(axis=1)
    yaxis2_text=pd.concat([total_actual_mrr,total_contract_mrr],axis=1)

    yaxis2_text.reset_index(drop=True,inplace=True)
    yaxis2_text.columns=['Actual MRR','Contract MRR']
    yaxis2_text['text']=yaxis2_text.apply(lambda row: '{:,.0f}/{:,.0f} \t ({:.0%})'.format(row['Actual MRR'],row['Contract MRR'],row['Actual MRR']/row['Contract MRR']),axis=1)
    yaxis2_text=yaxis2_text['text'].to_dict()


    #add right hand y-axis for additional information
    top=max(yaxis2_text.keys())
    bottom=min(yaxis2_text.keys())
    print(top,bottom)

    hm.extra_y_ranges={'mrr':Range1d(top,bottom)}

    hm.add_layout(LinearAxis(y_range_name="mrr"), 'right')

    hm.yaxis[1].formatter=FuncTickFormatter(code="""var labels = {};
                                                 return labels[tick];
                                                 """.format(yaxis2_text))
    hm.yaxis[1].ticker = FixedTicker(ticks=list(yaxis2_text.keys()))
    hm.yaxis[1].axis_label='Actual and Contract MRR'
    hm.yaxis[1].major_label_standoff=30

    # #help(hm.legend)
    # legend_items=list(hm.legend)[0].items
    #

    hm.legend.location='bottom_right'

    # exit()
    output_file('interactive.html')
    show(hm)

bokeh_heatmap(index=['Industry','Representative','Date'])
