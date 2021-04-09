# Nokia-Static-Routes
Script to fix static routes definition for a mobile network Nokia based


Code description:

    -reads an Excel file with sites static routes configuration from the a Nokia based network
    
    -imports this table into a DataFrame
    
    -links GW address to each IP
    
    -completes configuration in case of missing IP adresses, but also keeps all the non-standard IP (customized IP)
    
    -generation of XML given data processed in DataFrames for both Flexi and SRAN nodes
