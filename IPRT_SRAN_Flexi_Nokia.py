# -*- coding: utf-8 -*-
"""
Created on Mon Aug 24 17:02:13 2020

@author: Pablo La Grutta
email: pablo.lg.unlam@gmail.com

Code description:
    -read an Excel file with sites static routes configuration from the a Nokia based network
    -imports this table into a DataFrame
    -links GW address to each IP
"""

import pandas as pd
import re
import os


path = os.path.abspath("path/to/network/static/routes/file.xlsx") 

df_source = pd.read_excel(path,sheet_name="LTE-SRAN-Flexi", index_col = None)
df_source = df_source.astype(str)
df_source = df_source[['DN_MRBTS','DN_LNBTS','bfdId','destinationIpPrefixLength','destIpAddr','gateway','netmask','preference','preSrcIpv4Addr']]

df_source.rename(columns = {'DN_MRBTS':'MRBTS','gateway':'gw','destinationIpPrefixLength':'length','destIpAddr':'dest','preference':'pref','preSrcIpv4Addr':'preSrc'}, inplace=  True)
df_Flexi = df_source.loc[df_source['DN_LNBTS']!="-1"]
df_SRAN = df_source.loc[df_source['DN_LNBTS']=="-1"]
df_SRAN = df_SRAN[['MRBTS','dest','gw','length','pref','preSrc']]
df_Flexi.drop(columns=["DN_LNBTS","length"],inplace=True)


""""

SRAN algorithm

"""
df = df_SRAN

df['prop'] = df[['gw','length','pref','preSrc']].values.tolist()


###--links GW to each existent IP
df['dict_prop']=df.apply(lambda row: {row['dest']:row['prop']}, axis=1)
df.fillna(value='falso',inplace=True)
listaRegex_dest_total = [r"10.102.*",r"10.107.*",r"10.106.*",r"10.104.*"]
lista_full_dest_total = ['10.102.0.0','10.104.0.0','10.106.0.0','10.107.0.0']
lista_init_dest_total = ['10.104','10.106','10.102','10.107']
lista_A = [r'10.102.+',r'10.107.+']
lista_B =[r'10.106.+',r'10.104.+']
dict_A={'10.102.':'10.107','10.107':'10.102'} ##-- for each IP starting with 10.102., link to 10.107, and backwards
dict_B={'10.104':'10.106','10.106':'10.104'}
dictComplem = {'10.102.0.0':'10.107.0.0','10.107.0.0':'10.102.0.0','10.104.0.0':'10.106.0.0','10.106.0.0':'10.104.0.0'}

listaRegex_dest_total = re.compile (('|'.join(listaRegex_dest_total)))

df2 = df.groupby(['MRBTS']).apply(lambda x: [list(x['dest']), list(x['gw']),list(x['length']),list(x['pref']),list(x['preSrc']),list(x['prop'])]).apply(pd.Series)#.reset_index(name='listas')
df2.rename(columns={0:'lista_dest_actual',1:'lista_gw_actual',2:'lista_length_actual',3:'lista_pref_actual',4:'lista_preSrc_actual',5:'lista_prop_actual'},inplace=True)


df2['dict_prop'] = df2.apply(lambda row: dict(zip(row['lista_dest_actual'], row['lista_prop_actual'])),axis=1)


###--calculation of how many of current IP belongs to LTE configuration
df2['LTE'] = df2['lista_dest_actual'].apply(lambda x:len([any(i) for e in lista_init_dest_total for i in x if e in i] )) 
###-- if null, drop them
df2 = df2.loc[df2['LTE']!=0]

df2['match_dest_o_1'] = df2['lista_dest_actual'].apply(lambda x:[ listaRegex_dest_total.findall(i) for i in x]) #[listaRegex_dest_total.findall(i) for i in  x.item for x in  df2['lista_dest_actual']]
df2['match_dest_o_4'] = df2['match_dest_o_1'].apply(lambda x: [item for sublist in x for item in sublist])
df2['match_dest_o_2'] = df2['match_dest_o_1'].apply(lambda x: [item for sublist in x for item in sublist])
df2['match_dest_o_3'] = df2['match_dest_o_2']
for x in df2['match_dest_o_3']:
    for n,item in enumerate(x):
        if(item.startswith('10.104')):
            x[n] = '10.104.0.0'
        elif (item.startswith('10.102')):
            x[n] = '10.102.0.0'
        elif (item.startswith('10.106')):
            x[n] = '10.106.0.0'
        elif (item.startswith('10.107')):
            x[n] = '10.107.0.0'
df2['match_dest_f'] = df2['match_dest_o_3']


df2['match_prop']= df2.apply(lambda row: [x if x not in row['dict_prop'] else row['dict_prop'][x] for x in row['match_dest_o_4']],axis=1)

df2['match_gw']= df2.apply(lambda row: [x if x not in row['dict_prop'] else row['dict_prop'][x][0] for x in row['match_dest_o_4'] ],axis=1)
df2['match_length']= df2.apply(lambda row: [x if x not in row['dict_prop'] else row['dict_prop'][x][1] for x in row['match_dest_o_4'] ],axis=1)
df2['match_pref']= df2.apply(lambda row: [x if x not in row['dict_prop'] else row['dict_prop'][x][2] for x in row['match_dest_o_4'] ],axis=1)
df2['match_preSrc']= df2.apply(lambda row: [x if x not in row['dict_prop'] else row['dict_prop'][x][3] for x in row['match_dest_o_4'] ],axis=1)





df2['ipComplem'] = df2.apply(lambda row: [x if x not in dictComplem else dictComplem[x] for x in row['match_dest_o_3']],axis=1)
df2['ip_faltan'] = set(lista_full_dest_total) - df2['match_dest_f'].map(set)
df2['ip_faltan'] = df2['ip_faltan'].apply(lambda x: list(x))
df2['ip_final'] = df2['lista_dest_actual'] + df2['ip_faltan']  ##--IP final con las IP customizadas fuera de norma

df2['dict_gw'] =  df2.apply(lambda row: dict(zip(row['ipComplem'],row['match_gw'])),axis=1) #--dict e/ la ipComplementaria y el match_gw
df2['dict_length'] =  df2.apply(lambda row: dict(zip(row['ipComplem'],row['match_length'] )),axis=1) #--dict e/ la ipComplementaria y el match_gw
df2['dict_pref'] =  df2.apply(lambda row: dict(zip(row['ipComplem'],row['match_pref'] )),axis=1) #--dict e/ la ipComplementaria y el match_gw
df2['dict_preSrc'] =  df2.apply(lambda row: dict(zip(row['ipComplem'],row['match_preSrc'] )),axis=1) #--dict e/ la ipComplementaria y el match_gw


df2['gw_faltan'] = df2.apply(lambda row: [x if x not in row['dict_gw'] else row['dict_gw'][x] for x in row['ip_faltan']],axis=1)                                                    
df2['length_faltan'] = df2.apply(lambda row: [x if x not in row['dict_length'] else row['dict_length'][x] for x in row['ip_faltan']],axis=1)                                                    
df2['pref_faltan'] = df2.apply(lambda row: [x if x not in row['dict_pref'] else row['dict_pref'][x] for x in row['ip_faltan']],axis=1)                                                    
df2['preSrc_faltan'] = df2.apply(lambda row: [x if x not in row['dict_preSrc'] else row['dict_preSrc'][x] for x in row['ip_faltan']],axis=1)                                                    




df2['gw_final'] = df2['lista_gw_actual'] + df2['gw_faltan']
df2['length_final'] = df2['lista_length_actual'] + df2['length_faltan']
df2['pref_final'] = df2['lista_pref_actual'] + df2['pref_faltan']
df2['preSrc_final'] = df2['lista_preSrc_actual'] + df2['preSrc_faltan']


##--broadcasting of index, ip_final, ip_final_c, gw_final
df3 = df2[['ip_final','gw_final','length_final','pref_final','preSrc_final']]


df3 = df3.apply(pd.Series.explode).reset_index()

df3.rename(columns = {'ip_final':'destIpAddr','gw_final':'gateway','length_final':'destinationIpPrefixLength','pref_final':'preference','preSrc_final':'preSrcIpv4Addr'}, inplace=  True)


df_final_SRAN = df3

"""

FLEXI algorithm

"""
dfF = df_Flexi

dfF['prop'] = dfF[['gw','pref','preSrc','bfdId','netmask']].values.tolist()

print("Flexi",dfF.head())

###--link GW to each existent IP
dfF['dict_prop']=dfF.apply(lambda row: {row['dest']:row['prop']}, axis=1)
dfF.fillna(value='falso',inplace=True)
listaRegex_dest_total = [r"10.102.*",r"10.107.*",r"10.106.*",r"10.104.*"]
lista_full_dest_total = ['10.102.0.0','10.104.0.0','10.106.0.0','10.107.0.0']
lista_init_dest_total = ['10.104','10.106','10.102','10.107']
lista_A = [r'10.102.+',r'10.107.+']
lista_B =[r'10.106.+',r'10.104.+']
dict_A={'10.102.':'10.107','10.107':'10.102'} ##-- para toda IP que contenga 10.102., asociar 10.107, y viceversa
dict_B={'10.104':'10.106','10.106':'10.104'} ##-- para toda IP que contenga 10.104., asociar 10.106, y viceversa
dictComplem = {'10.102.0.0':'10.107.0.0','10.107.0.0':'10.102.0.0','10.104.0.0':'10.106.0.0','10.106.0.0':'10.104.0.0'}
listaRegex_dest_total = re.compile (('|'.join(listaRegex_dest_total)))

dfF2 = dfF.groupby(['MRBTS']).apply(lambda x: [list(x['dest']), list(x['gw']),list(x['pref']),list(x['preSrc']),list(x['bfdId']),list(x['netmask']),list(x['prop'])]).apply(pd.Series)#.reset_index(name='listas')

dfF2.rename(columns={0:'lista_dest_actual',1:'lista_gw_actual',2:'lista_pref_actual',3:'lista_preSrc_actual',4:'lista_bfdId_actual',5:'lista_netmask_actual',6:'lista_prop_actual'},inplace=True)


dfF2['dict_prop'] = dfF2.apply(lambda row: dict(zip(row['lista_dest_actual'], row['lista_prop_actual'])),axis=1)

###--calculation of how many IP belongs to LTE configuration
dfF2['LTE'] = dfF2['lista_dest_actual'].apply(lambda x:len([any(i) for e in lista_init_dest_total for i in x if e in i] )) 
###-- if null, drop them
dfF2 = dfF2.loc[dfF2['LTE']!=0]

dfF2['match_dest_o_1'] = dfF2['lista_dest_actual'].apply(lambda x:[ listaRegex_dest_total.findall(i) for i in x]) #[listaRegex_dest_total.findall(i) for i in  x.item for x in  dfF2['lista_dest_actual']]
dfF2['match_dest_o_4'] = dfF2['match_dest_o_1'].apply(lambda x: [item for sublist in x for item in sublist])
dfF2['match_dest_o_2'] = dfF2['match_dest_o_1'].apply(lambda x: [item for sublist in x for item in sublist])
dfF2['match_dest_o_3'] = dfF2['match_dest_o_2']
for x in dfF2['match_dest_o_3']:
    for n,item in enumerate(x):
        if(item.startswith('10.104')):
            x[n] = '10.104.0.0'
        elif (item.startswith('10.102')):
            x[n] = '10.102.0.0'
        elif (item.startswith('10.106')):
            x[n] = '10.106.0.0'
        elif (item.startswith('10.107')):
            x[n] = '10.107.0.0'
dfF2['match_dest_f'] = dfF2['match_dest_o_3']


dfF2['match_prop']= dfF2.apply(lambda row: [x if x not in row['dict_prop'] else row['dict_prop'][x] for x in row['match_dest_o_4']],axis=1)

dfF2['match_gw']= dfF2.apply(lambda row: [x if x not in row['dict_prop'] else row['dict_prop'][x][0] for x in row['match_dest_o_4'] ],axis=1)
dfF2['match_pref']= dfF2.apply(lambda row: [x if x not in row['dict_prop'] else row['dict_prop'][x][1] for x in row['match_dest_o_4'] ],axis=1)
dfF2['match_preSrc']= dfF2.apply(lambda row: [x if x not in row['dict_prop'] else row['dict_prop'][x][2] for x in row['match_dest_o_4'] ],axis=1)
dfF2['match_bfdId'] = dfF2.apply(lambda row: [x if x not in row['dict_prop'] else row['dict_prop'][x][3] for x in row['match_dest_o_4'] ],axis=1)
dfF2['match_netmask'] = dfF2.apply(lambda row: [x if x not in row['dict_prop'] else row['dict_prop'][x][4] for x in row['match_dest_o_4'] ],axis=1)

dfF2['ipComplem'] = dfF2.apply(lambda row: [x if x not in dictComplem else dictComplem[x] for x in row['match_dest_o_3']],axis=1)
dfF2['ip_faltan'] = set(lista_full_dest_total) - dfF2['match_dest_f'].map(set)
dfF2['ip_faltan'] = dfF2['ip_faltan'].apply(lambda x: list(x))
dfF2['ip_final'] = dfF2['lista_dest_actual'] + dfF2['ip_faltan']  ##--final IP with customized IP out of rule

dfF2['dict_gw'] =  dfF2.apply(lambda row: dict(zip(row['ipComplem'],row['match_gw'])),axis=1) #--dict made with  ipComplementaria and match_gw
dfF2['dict_pref'] =  dfF2.apply(lambda row: dict(zip(row['ipComplem'],row['match_pref'] )),axis=1) 
dfF2['dict_preSrc'] =  dfF2.apply(lambda row: dict(zip(row['ipComplem'],row['match_preSrc'] )),axis=1) 
dfF2['dict_bfdId'] = dfF2.apply(lambda row: dict(zip(row['ipComplem'],row['match_bfdId'] )),axis=1)
dfF2['dict_netmask'] = dfF2.apply(lambda row: dict(zip(row['ipComplem'],row['match_netmask'] )),axis=1)

dfF2['gw_faltan'] = dfF2.apply(lambda row: [x if x not in row['dict_gw'] else row['dict_gw'][x] for x in row['ip_faltan']],axis=1)  
dfF2['pref_faltan'] = dfF2.apply(lambda row: [x if x not in row['dict_pref'] else row['dict_pref'][x] for x in row['ip_faltan']],axis=1)  
dfF2['preSrc_faltan'] = dfF2.apply(lambda row: [x if x not in row['dict_preSrc'] else row['dict_preSrc'][x] for x in row['ip_faltan']],axis=1)                                                    
dfF2['bfdId_faltan'] = dfF2.apply(lambda row: [x if x not in row['dict_bfdId'] else row['dict_bfdId'][x] for x in row['ip_faltan']],axis=1)     
dfF2['netmask_faltan'] = dfF2.apply(lambda row: [x if x not in row['dict_netmask'] else row['dict_netmask'][x] for x in row['ip_faltan']],axis=1)     

dfF2['gw_final'] = dfF2['lista_gw_actual'] + dfF2['gw_faltan']
dfF2['pref_final'] = dfF2['lista_pref_actual'] + dfF2['pref_faltan']
dfF2['preSrc_final'] = dfF2['lista_preSrc_actual'] + dfF2['preSrc_faltan']
dfF2['bfdId_final'] =  dfF2['lista_bfdId_actual'] + dfF2['bfdId_faltan']
dfF2['netmask_final'] =   dfF2['lista_netmask_actual'] + dfF2['netmask_faltan']


##--broadcasting of index, ip_final, ip_final_c, gw_final
dfF3 = dfF2[['ip_final','gw_final','pref_final','preSrc_final','bfdId_final','netmask_final']]


dfF3 = dfF3.apply(pd.Series.explode).reset_index()

dfF3.rename(columns = {'ip_final':'destIpAddr','gw_final':'gateway','pref_final':'preference','preSrc_final':'preSrcIpv4Addr','bfdId_final':'bfdId','netmask_final':'netmask'}, inplace=  True)


dfF_final_Flexi= dfF3