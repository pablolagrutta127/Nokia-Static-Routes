# -*- coding: utf-8 -*-
"""
Created on Mon Aug 24 17:02:13 2020

@author: Pablo La Grutta
email: pablo.lg.unlam@gmail.com

Code description:
    -generation of XML given data processed in DataFrames
"""

import lxml.etree as et

from IPRT_SRAN_Flexi import dfF_final_Flexi

"""
##--Flexi: PLMN-PLMN/MRBTS-130078/LNBTS-130078/FTM-1/IPNO-1/IPRT-1  

"""       
### STATIC PART OF XML
rootF = et.Element('raml', {"version": "2.0", "xmlns": "raml20.xsd"})

cmDataF = et.SubElement(rootF, "cmData",
                       {"type":"plan", "scope":"all", "name":"iprt", "id":"PlanConfiguration( 7152069 )"})

headerF = et.SubElement(cmDataF, "header")
logF = et.SubElement(headerF, "log",
                    {"dateTime":"2020-06-19T07:38:16.000-03:00", "action":"created", "appInfo":"PlanExporter"})
logF.text = "InternalValues are used"

dfF = dfF_final_Flexi.astype(str)
for I, G in dfF.groupby("MRBTS"):
    MO = et.SubElement(cmDataF, "managedObject", {"class":"IPRT", "distName":"PLMN-PLMN/MRBTS-"+I+"/LNBTS"+I+"/FTM-1/IPNO-1/IPRT-1", "operation":"update"})
    list = et.SubElement(MO, "list",{"name":"staticRoutes"})
    
    # BUILD DICTIONARY OUT OF EACH ROW
    D = G.drop('MRBTS', axis='columns').to_dict('index')
    
    for IK, IV in D.items():
        itemF = et.SubElement(list, 'item')
        for K, V in IV.items():
            P = et.SubElement(itemF, 'p', {"name":K})
            P.text = V
   



# OUTPUT TREE
treeF = et.ElementTree(rootF)
tree_outF = treeF.write("Output_Flexi.xml",
                      xml_declaration=True, 
                      encoding="UTF-8",
                      pretty_print=True,
                      doctype="<!DOCTYPE raml SYSTEM 'raml20.dtd'>")



with open('Output_Flexi.xml','r') as fF:
    docF=et.parse(fF)
    for elemF in docF.xpath('//*[attribute::name]'):
        if elemF.attrib['name']=='nan':
            parentF=elemF.getparent()
            parentF.remove(elemF)

    print(et.tostring(docF))

#input file
finF = open("Output_Flexi.xml", "rt")
#output file to write the result to
foutF = open("Output_Flexi_final.xml", "wt")
#for each line in the input file
for lineF in finF:
	#read replace the string and write to output file
    foutF.write(lineF.replace('>nan</p>', '/>').replace('>0.0<', '>0<'))
  
#close input and output files
finF.close()
foutF.close()