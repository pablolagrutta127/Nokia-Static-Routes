# -*- coding: utf-8 -*-
"""
Created on Mon Aug 24 17:02:13 2020

@author: Pablo La Grutta
email: pablo.lg.unlam@gmail.com

Code description:
    -generation of XML given data processed in DataFrames
"""

import lxml.etree as et

from IPRT_SRAN_Flexi_Nokia import df_final_SRAN


### STATIC PART OF XML
root = et.Element('raml', {"version": "2.0", "xmlns": "raml20.xsd"})

cmData = et.SubElement(root, "cmData",
                       {"type":"plan", "scope":"all", "name":"iprt", "id":"PlanConfiguration( 7152069 )"})

header = et.SubElement(cmData, "header")
log = et.SubElement(header, "log",
                    {"dateTime":"2020-06-19T07:38:16.000-03:00", "action":"created", "appInfo":"PlanExporter"})
log.text = "InternalValues are used"

### DYNAMIC PART OF XML
"""
df = pd.DataFrame({'MRBTS':['13004','13004','13005','13005','13005'],
                   'dest':['10.104.0.0','10.107.0.0','10.104.0.0','10.102.0.0','0.0.0.0'],
                   'gw':['10.48.0.0','10.45.0.0','10.130.0.0','10.130.0.0','10.110.0.0'],
                   'length':['16','16','8','8','nan']})

"""
df = df_final_SRAN.astype(str)



# SUBSET ITERATION        
##--Flexi: PLMN-PLMN/MRBTS-130078/LNBTS-130078/FTM-1/IPNO-1/IPRT-1         
for i, g in df.groupby("MRBTS"):
    managedObject = et.SubElement(cmData, "managedObject", {"class":"IPRT", "distName":"PLMN-PLMN/MRBTS-"+i+"/TNLSVC-1/TNL-1/IPNO-1/IPRT-1", "operation":"update"})
    list = et.SubElement(managedObject, "list",{"name":"staticRoutes"})
    
    # BUILD DICTIONARY OUT OF EACH ROW
    d = g.drop('MRBTS', axis='columns').to_dict('index')
    
    for ik, iv in d.items():
        item = et.SubElement(list, 'item')
        for k, v in iv.items():
            p = et.SubElement(item, 'p', {"name":k})
            p.text = v




# OUTPUT TREE
tree = et.ElementTree(root)
tree_out = tree.write("Output_SRAN.xml",
                      xml_declaration=True, 
                      encoding="UTF-8",
                      pretty_print=True,
                      doctype="<!DOCTYPE raml SYSTEM 'raml20.dtd'>")



with open('Output_SRAN.xml','r') as f:
    doc=et.parse(f)
    for elem in doc.xpath('//*[attribute::name]'):
        if elem.attrib['name']=='nan':
            parent=elem.getparent()
            parent.remove(elem)

    print(et.tostring(doc))

#input file
fin = open("Output_SRAN.xml", "rt")
#output file to write the result to
fout = open("Output_SRAN_final.xml", "wt")
#for each line in the input file
for line in fin:
	#read replace the string and write to output file
    fout.write(line.replace('>nan</p>', '/>').replace('>1.0<', '>1<'))
  
#close input and output files
fin.close()
fout.close()

