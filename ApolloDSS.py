#!/usr/bin/env python
# coding: utf-8


#conda create --name streamlit python=3.8
#!pip install streamlit 

#----------------------------------------------------------------------------------------------------------------
# LIBRARIES
# ~~~~~~~~~

import streamlit as st 
from PIL import Image
import os
from datetime import datetime
import base64

import altair as alt
#import matplotlib.pyplot as plt 
#import matplotlib
#matplotlib.use("Agg")
import seaborn as sns
import pandas as pd 
import numpy as np
pd.options.display.max_colwidth = 10
#----------------------------------------------------------------------------------------------------------------
# WEBPAGE GENERAL ITEMS
# ~~~~~~~~~~~~~~~~~~~~

#Setting file path
path = os.path.dirname(__file__)

#Displaying Apollo Banner
my_file = path+'/images/ApolloBanner.jpg'
img=Image.open(my_file)
st.image(img,width=700)

#Displaying IIMB logo in sidebar
img=Image.open(path+'/images/iimb.png')
st.sidebar.image(img,width=300)

#Sidebar page navigation title
st.sidebar.title("Login")

#Sidebar page navigation
user = st.sidebar.selectbox("Select user ID:",("Jeyasri Ramesh (Doctor)","Amrata Agrawal (Typist)", "Sharan Sivakumar (Doctor)","Harsh Upadhyay (Typist)","Admin"))


#Sidebar page navigation title
st.sidebar.title("Navigation Pane")
page = st.sidebar.radio("You are currently in:",("Prescription DSS", "Indent DSS","Dashboard"))

#Proxy login
if user == "Admin":
    page = "Dashboard"
elif user == "Amrata Agrawal (Typist)" or user == "Harsh Upadhyay (Typist)":
    page = "Indent DSS"
else:
    page = "Prescription DSS"
    





#----------------------------------------------------------------------------------------------------------------
#LOADING REFERENCE FILES 
#~~~~~~~~~~~~~~~~~~~~~~~~
@st.cache(show_spinner=False)
def load_data():
    #Riz_rules_apriori_dfeference sheet with frequent sets from Apriori - overall indents
    biz_rules_apriori_df = pd.read_excel(path+ '/data/Apollo_biz_rules.xlsx', sheet_name = "Apriori-all")  

    #Reference sheet with caution info for generic names
    biz_rules_caution_df = pd.read_excel(path+ '/data/Apollo_biz_rules.xlsx', sheet_name = "Caution")

    #Reference sheet with allergy info for generic names
    biz_rules_Allergy_df = pd.read_excel(path+ '/data/Apollo_biz_rules.xlsx', sheet_name = "Allergy")

    #Reference sheet with drug interaction info for generic names
    biz_rules_DI_df = pd.read_excel(path+ '/data/Apollo_biz_rules.xlsx', sheet_name = "Drug Interaction")

    #Reference sheet with Medicine name, drug code, generic name
    drug_df = pd.read_excel(path+ '/data/Apollo_biz_rules.xlsx', sheet_name = 'Drugs_ref')  

    #Complete indentsheet of Jubilee Hills 2019
    indent_df = pd.read_csv(path+ '/data/FullIndents_FinalVersion_Masked.csv') 

    #Reference sheet with drug interaction info for generic names
    biz_rules_ward_df = pd.read_excel(path+ '/data/Apollo_biz_rules.xlsx', sheet_name = "wards") 
    
    return biz_rules_apriori_df,biz_rules_caution_df,biz_rules_Allergy_df,biz_rules_DI_df,drug_df,indent_df,biz_rules_ward_df


biz_rules_apriori_df,biz_rules_caution_df,biz_rules_Allergy_df,biz_rules_DI_df,drug_df,indent_df,biz_rules_ward_df = load_data()
indent_df['IPNUMBER']=indent_df['IPNUMBER'].astype(str)
#st.write(type(indent_df['IPNUMBER'][0]))
#Reference sheet with log info for dashboard
dash_df = pd.read_csv(path+ '/data/dashboard.csv')  

#----------------------------------------------------------------------------------------------------------------
# FUNCTIONS
# ~~~~~~~~~

#Dislaying warning or info icon on runtime
def set_flag(flag):
	if flag ==1:
		return "<center><img src='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSvv9YYqFZSx-lvU8ws56OSVIdZ7R1BI4rOqQ&usqp=CAU' width=30></img></center>"
	else:
		return "<center><img src='https://upload.wikimedia.org/wikipedia/commons/thumb/2/25/Info_icon-72a7cf.svg/1200px-Info_icon-72a7cf.svg.png' width=30></img></center>"

#Flattens a list
def flatten_list(apriori_list, generic_name):
    flattened_apriori_list = []
    for index in range(len(apriori_list)):
        temp = apriori_list[index].split(",")
        temp = [i.strip() for i in temp]
        #st.write(temp, generic_name)
        if generic_name in temp: #To check false positive results from "contains" df filter
            position = temp.index(generic_name)
            del temp[position]
            flattened_apriori_list.extend(temp)
        else:
            pass
    if len(flattened_apriori_list) > 0:
        flattened_apriori_list= list(set(flattened_apriori_list))

    return flattened_apriori_list
      
#Generate alert text    
def get_alertText_flags(flag_df):
    pretext_1 = "NOT RECOMMENDED for "
    pretext_2 = "RECONSIDER dosage for "
    #List order -> Pregnancy, Breastfeeding, Kidney, Liver
    #List values -> 0 - no issue, 1 - Avoid, 2 - Reconsider medicine and dosage
    flag_code = [1,2]
    text = ""
    caution = ""
    alert_type = 0
    for item in flag_code:
        flag_list = list(flag_df.columns[(flag_df == item).any(axis=0)])
        if len(flag_list) > 0:
            caution = "Drug caution"
            if item == 1:
                text = text + pretext_1 + " , ".join(flag_list) + ". "
            else:
                text = text + pretext_2 + " , ".join(flag_list) + "."
        else:
            text = ""
    #st.write("IN")
    #st.write(caution, text, alert_type)
    return caution, text, alert_type, alert_type

        
#----------------------------------------------------------------------------------------------------------------	
# MAIN PAGE
# ~~~~~~~~~	


#Global variables
pres_IP = ""
existing_gen_names=[]
updated_missing_drug_list=[]

#Dataframe that stores indent records filtered by entered IP
IP_df = pd.DataFrame() 

#Dataframe that stores currently prescribed medicine related information
medicine_df = pd.DataFrame(columns=['MEDICINENAME','GENERICNAME','Pregnant women','Kidney patients','Liver patients','Breastfeeding women','Missingdrug_flag','MissingDrugs']) 

#Dataframe to display analysis
analysis_df = pd.DataFrame(columns = ['MEDICINENAME','ALERT_CATEGORY','ALERT_MESSAGE','ALERT_TYPE','Flag'])



##### PRESCRIPTION DSS PAGE

if page == "Prescription DSS":
    #load_data()
    #-------------------------------------------------------------------------------------------------------------
    #Input from user
    # ~~~~~~~~~~~~~~
	
    
    #Title
    st.write("<h2><center> Prescription Decision Support System </center></h2>", unsafe_allow_html=True)

    pres_IP = st.text_input("Enter In-Patient number: ('IDxxxxxx')")
    audit_pres_button=0
    submit_pres_button=0
    ward=""
    pres_med=[]
    
    if len(pres_IP) > 0: #Check if IP is entered
 
        new_entry = 0
        Dates =[]
        
        #retrieve past 3 prescritions at max
        IP_df = indent_df[indent_df['IPNUMBER'] == str(pres_IP)][['CREATEDDATE','DRUGCODE','MEDICINENAME','MedicineType','Corrected_GenericNames','WARDNAME']].sort_values(by='CREATEDDATE', ascending=False )
        if len(IP_df['CREATEDDATE'].unique())>3:
            Dates = IP_df['CREATEDDATE'].unique()[:3]
            IP_df = IP_df[IP_df['CREATEDDATE'].isin(Dates)]
        elif len(IP_df['CREATEDDATE'].unique())>0:
            Dates = IP_df['CREATEDDATE'].unique()
            IP_df = IP_df[IP_df['CREATEDDATE'].isin(Dates)]
        else:
            new_entry = 1
        all_wards = list(indent_df['WARDNAME'].unique())
        default_index=0

        #Display recent prescriptions
        st.sidebar.subheader("Recent Prescriptions: " +pres_IP)
        if new_entry: 
            #st.write("New")
            st.sidebar.write("None")
        else:
            past_unique_gen_names = IP_df['Corrected_GenericNames'].unique()
            history_df = IP_df[['CREATEDDATE','MEDICINENAME']].set_index('CREATEDDATE')
            st.sidebar.dataframe(history_df['MEDICINENAME'])
            #st.write()
            current_ward = IP_df['WARDNAME'].tolist()[0].strip()
            default_index = all_wards.index(current_ward)
       
        #Select ward if new IP/ load ward from historical data
        ward = st.selectbox("Choose current ward :", all_wards,index = default_index) 

        #Enter medicines for prescription
        pres_med = st.multiselect("Enter all medicine names :", list(drug_df['MEDICINENAME'].unique()),[])
        st.write("<br>",unsafe_allow_html=True)
        
        #Button click action
        dummy1,dummy2,dummy3 = st.beta_columns(3)
        with dummy1:
            audit_pres_button = st.button("Audit Prescription")
            
        with dummy3:
            submit_pres_button = st.button("Submit Prescription")        
        
        #st.sidebar.write("<br>",unsafe_allow_html=True) 
        #Help information for substitute medicines
        st.sidebar.subheader("Find Substitute Medicines") 
        find_by_generic_name = st.sidebar.selectbox("Select Generic name:",drug_df['Corrected_GenericNames'].unique(),help="Verify dosage before prescribing.")
        suggest_medicine = drug_df[drug_df['Corrected_GenericNames'] == find_by_generic_name ]
        st.sidebar.write(suggest_medicine[['MEDICINENAME','MedicineType']].to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        st.error("Please enter IP number to proceed.")
   
    #-------------------------------------------------------------------------------------------------------------
    #Data analysis
    #~~~~~~~~~~~~~~ 
        
    #IP_df = indent_df[indent_df['IPNUMBER'] == str(pres_IP)][['DRUGCODE','MEDICINENAME','MedicineType','Corrected_GenericNames']]
    #st.dataframe(IP_df.head().style.hide_index())
    
    #Check medicines are entered
    if len(pres_med)>0:
        
        medicine_df = pd.DataFrame(columns= medicine_df.columns)
        analysis_df = pd.DataFrame(columns= analysis_df.columns)
        
        #pres_med = [x.strip() for x in pres_med]
        medicine_df['MEDICINENAME']= pres_med
        #st.write(medicine_df)
        for x in range(len(medicine_df)):
            generic_name = drug_df['Corrected_GenericNames'][drug_df['MEDICINENAME'] == medicine_df['MEDICINENAME'][x]].values[0]
            #st.write(medicine_df['MEDICINENAME'][x])
            #st.write(x, generic_name)
            medicine_df['GENERICNAME'][x] = generic_name
            
        
            #Drug caution--------------------------------
            #Fetching caution information
            #Flag values: 0 - No issue, 1 - Avoid, 2 - Reconsider/ Adjust dosage
            medicine_df['Pregnant women'][x] = biz_rules_caution_df['Pregnancy_flag'][biz_rules_caution_df['GenericName'] == generic_name].values[0]
            medicine_df['Kidney patients'][x] = biz_rules_caution_df['Kidney_flag'][biz_rules_caution_df['GenericName'] == generic_name].values[0]
            medicine_df['Liver patients'][x] = biz_rules_caution_df['Liver_flag'][biz_rules_caution_df['GenericName'] == generic_name].values[0]
            medicine_df['Breastfeeding women'][x] = biz_rules_caution_df['Breastfeeding_flag'][biz_rules_caution_df['GenericName'] == generic_name].values[0]
            #Drug caution-------------------------------
        
        
            #Missing drugs------------------------------
            if len(biz_rules_apriori_df[biz_rules_apriori_df['itemsets'].str.contains(generic_name)].sort_values(by = 'support', ascending = False).head(10)) > 0:
                apriori_list = biz_rules_apriori_df[biz_rules_apriori_df['itemsets'].str.contains(generic_name)].sort_values('support', ascending = False)['itemsets'].head(10).values
                #st.write(list(apriori_list))
                flattened_apriori_list = flatten_list(apriori_list, generic_name)
                if len(flattened_apriori_list) > 0 :
                    medicine_df['Missingdrug_flag'][x]=1
                    medicine_df['MissingDrugs'][x] = flattened_apriori_list
                    #st.write(flattened_apriori_list)
                else:
                    medicine_df['Missingdrug_flag'][x]=0
                    medicine_df['MissingDrugs'][x]=""
        
            
            else:
                medicine_df['Missingdrug_flag'][x]=0
                medicine_df['MissingDrugs'][x]=""
            #Missing drugs---------------------------------    
    
    
        existing_gen_names = list(medicine_df['GENERICNAME'])
    
        #Therapeutic duplication/overdose-----------------------------
        flat_gen_name_df = pd.DataFrame(columns = ['index','medicine_name','original_gen','flat_gen'])
        #Flatten list
        #dupes = [n, x for n, x in enumerate(existing_gen_names) if x in existing_gen_names[:n]]
        for x in range(len(existing_gen_names)):
            if existing_gen_names[x].find('+') > -1:
                temp = existing_gen_names[x].split("+")
                temp = [i.strip() for i in temp]
                for item in temp:
                    dup_record = [x,medicine_df['MEDICINENAME'][x],existing_gen_names[x],item]
                    flat_gen_name_df = flat_gen_name_df.append(dict(zip(flat_gen_name_df.columns, dup_record)), ignore_index = True)
            else:
                item= existing_gen_names[x].strip()
                dup_record = [x,medicine_df['MEDICINENAME'][x],existing_gen_names[x],item]
                flat_gen_name_df = flat_gen_name_df.append(dict(zip(flat_gen_name_df.columns, dup_record)), ignore_index = True)
        duplicate_gen_names = list(set(flat_gen_name_df['flat_gen'][flat_gen_name_df.duplicated('flat_gen')]))
        duplicates_df = flat_gen_name_df[flat_gen_name_df['flat_gen'].isin(duplicate_gen_names)]
        #drop_duplicates_df = duplicates_df.drop_duplicates(subset='flat_gen', keep='first')
        exact_gen_duplicates = duplicates_df[duplicates_df.duplicated('original_gen')]  #Overdose
        #st.dataframe(exact_gen_duplicates)
        if len(exact_gen_duplicates) > 0:
            for row in exact_gen_duplicates.iterrows():
                #st.write(row[1]['flat_gen'])
                overdose_alert_text = row[1]['flat_gen'] + " has been prescribed more than once. Please check dosage."
                overdose_alert = [row[1]['medicine_name'],'Drug overdose',overdose_alert_text,1,1]
                analysis_df = analysis_df.append(dict(zip(analysis_df.columns, overdose_alert)), ignore_index = True)
        subset_gen_name_duplicates = pd.concat([duplicates_df,exact_gen_duplicates]).drop_duplicates(keep=False) #Therapeutic duplication
        #st.dataframe(subset_gen_name_duplicates)
        if len(subset_gen_name_duplicates ) > 0:
            for row in subset_gen_name_duplicates .iterrows():
                #st.write(row[1]['flat_gen'])
                ther_dup_alert_text = row[1]['flat_gen'] + " has being found in the composition of another medicine also."
                ther_dup_alert = [row[1]['medicine_name'],'Therapeutic duplication',ther_dup_alert_text,1,1]
                analysis_df = analysis_df.append(dict(zip(analysis_df.columns, ther_dup_alert)), ignore_index = True)
        exact_medicine_duplicates=exact_gen_duplicates[exact_gen_duplicates.duplicated('medicine_name')] #Drug continuity 
        #st.dataframe(flat_gen_name_df )
        #st.dataframe(duplicates_df)
        #st.dataframe(exact_gen_duplicates)
        #st.dataframe(subset_gen_name_duplicates)
    
    
        for x in range(len(medicine_df)):
           
            #Missing drugs--------------------------
            #Check for existing drugs against the missing drug list and update the missing drugs list.
            if medicine_df['Missingdrug_flag'][x] == 1:
                updated_missing_drug_list.extend(list(set(medicine_df['MissingDrugs'][x]) - set(existing_gen_names)))
                medicine_df['Missingdrug_flag'][x]=0
                medicine_df['MissingDrugs'][x]=""
            #Missing drugs--------------------------    
        
            #Allergy-------------------------------- 
            allergy = biz_rules_Allergy_df['Allergy_flag'][biz_rules_Allergy_df['Generic name']==medicine_df['GENERICNAME'][x]]
            if len(allergy) > 0:
                allergy_alert_text = "AVOID prescribing if patient is allergic towards " + allergy.values[0] +"."
                allergy_record = [medicine_df['MEDICINENAME'][x],'Allergy',allergy_alert_text,1,1]
                analysis_df = analysis_df.append(dict(zip(analysis_df.columns, allergy_record)), ignore_index = True)
            #Allergy--------------------------------
         
            #Drug caution---------------------------
            caution_alert = list(get_alertText_flags(medicine_df[medicine_df['MEDICINENAME']==medicine_df['MEDICINENAME'][x]]))
            #st.write(type(caution_alert))
            analysis_record=[]
            if len(caution_alert[0])>0:
                #st.write(caution_alert)
                caution_alert.insert(0,medicine_df['MEDICINENAME'][x])
                #st.write(caution_alert)
                analysis_df = analysis_df.append(dict(zip(analysis_df.columns, caution_alert)), ignore_index = True)
            #Drug caution-----------------------        
            
            
        #Drug Interaction----------------------- 
        unique_generic_names = list(set(existing_gen_names))
        DI_check_list = []
        DI_list =[]
        for gen_name in unique_generic_names:
            flag_drug=[row[1] for index, row in biz_rules_DI_df.iterrows() if gen_name.find(row[0]) > -1]
            if len(flag_drug) > 0:
                DI_check_list.append([gen_name, flag_drug])
        #st.write(DI_check_list)        
        for item in DI_check_list:
            excluded_genlist = unique_generic_names
            excluded_genlist.remove(item[0])
            for gen_name in excluded_genlist:
                DI_gen_name = [[gen_name, DI_item] for DI_item in item[1] if gen_name.find(DI_item) > -1]
                if len(DI_gen_name) >0:
                    DI_list.append([item[0], DI_gen_name])           
        
        #st.write(DI_list)
        for DI_item in DI_list:
            Med2 = Med1 = DI_Med1 = DI_Med2 = ""
            Med1_list= Med2_list=[]
            Med1_list=list(medicine_df['MEDICINENAME'][medicine_df['GENERICNAME']== DI_item[0]].values)
            Med1 = ", ".join(Med1_list)
            DI_Med1 = DI_item[0]
            #st.write(DI_item[1])
            if len(DI_item[1])>1:
                for item in DI_item[1]:
                    temp_med = list(medicine_df['MEDICINENAME'][medicine_df['GENERICNAME']== item[0]].values)
                    #st.write("in")
                    Med2_list.append(temp_med)
                    #st.write(Med2_list)
                    Med2 = ", ".join(Med2_list)
                    DI_Med2 = DI_Med2 + item[0] + " "
            else:
                Med2_list = list(medicine_df['MEDICINENAME'][medicine_df['GENERICNAME']== DI_item[1][0][0]].values)
                Med2 = ", ".join(Med2_list)
                #st.write(Med2)
                DI_Med2 = DI_item[1][0][0]
            #st.write("Cannot prescribe " +  Med1 + " along with " + Med2+ " due to "+ DI_Med1 +" - "+ DI_Med2 +" interaction.")
            DI_alert_text = "SHOULD NOT prescribe " +  Med1 + " along with " + Med2+ " due to "+ DI_Med1 +" - "+ DI_Med2 +" interaction."
            DI_alert_record = [Med1_list[0], "Drug Interaction", DI_alert_text, 1,1]
            analysis_df = analysis_df.append(dict(zip(analysis_df.columns, DI_alert_record)), ignore_index = True)
                         
        #Drug Interaction----------------------- 
            
            
        #Missing drugs -----------------        
        updated_missing_drug_list = list(set(updated_missing_drug_list))
        medicine_df['MissingDrugs'][0] = ", ".join(updated_missing_drug_list[:3])
    
        if len(updated_missing_drug_list) > 0: 
            medicine_df['Missingdrug_flag'][0]=1
        
        #if len(medicine_df) > 0:
            #st.write("Your prescription summary:")  
            #st.write(medicine_df[['MEDICINENAME','GENERICNAME']].to_html(escape=False, index=False), unsafe_allow_html=True)
            #st.write("<br>",unsafe_allow_html=True)
        
        if medicine_df['Missingdrug_flag'][0] == 1:
            #st.write("<br>",unsafe_allow_html=True)
            ###-> Convert to list type display
            html_str = "<img src='https://upload.wikimedia.org/wikipedia/commons/f/f6/Lol_question_mark.png' width=25></img><b> &nbsp Did you forget prescribing the following?</b> <br> "
            #st.components.v1.html(html_str, height=40, scrolling=False)
            loop = 1
            for item in medicine_df['MissingDrugs'][0].split(","):
                #st.write(str(loop)+". "+item.strip())
                loop +=1
        #Missing drugs ------------------
 
        #Calculate warnings and suggestions
        st.write("<br>",unsafe_allow_html=True)
        count_1 = str(len(analysis_df[analysis_df['Flag']>0]))
        count_0 = str(len(analysis_df[analysis_df['Flag']<1]))
        #war_count_str = "<b>"+ count_1 + "<style='color:red;font-family:arial'> Warning(s) (<img src='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSvv9YYqFZSx-lvU8ws56OSVIdZ7R1BI4rOqQ&usqp=CAU' width=10></img>) </style> and "+ count_0 +  "<style='color:blue;font-family:arial'> Suggestion(s) (<img src='https://upload.wikimedia.org/wikipedia/commons/thumb/2/25/Info_icon-72a7cf.svg/1200px-Info_icon-72a7cf.svg.png' width=10></img>)</style> identified.</b>"
        #st.components.v1.html(war_count_str, height=30, scrolling=False)
        #st.write("<br>",unsafe_allow_html=True)
    
        for x in range(len(analysis_df)):
            analysis_df['ALERT_TYPE'][x] = set_flag(int(analysis_df['ALERT_TYPE'][x]))
        
    elif len(pres_IP) > 0 & len(pres_med) < 1 :
        st.error("Please enter medicine names.")
    else: pass
    
    #Display Analysis information
    if audit_pres_button:
        if len(medicine_df) > 0:
            st.write("Your prescription summary:")  
            st.write(medicine_df[['MEDICINENAME','GENERICNAME']].to_html(escape=False, index=False), unsafe_allow_html=True)
            #st.write("<br>",unsafe_allow_html=True)
        if len(analysis_df) > 0:
            if medicine_df['Missingdrug_flag'][0] == 1:
                st.write("<br>",unsafe_allow_html=True)
                
                html_str = "<img src='https://upload.wikimedia.org/wikipedia/commons/f/f6/Lol_question_mark.png' width=20></img><b> &nbsp Did you forget prescribing any of the following?</b> <br> "
                st.components.v1.html(html_str, height=40, scrolling=False)
                loop = 1
                for item in medicine_df['MissingDrugs'][0].split(","):
                    st.write(str(loop)+". "+item.strip())
                    loop +=1
        st.write("<br>",unsafe_allow_html=True)    
        war_count_str = "<b>"+ count_1 + "<style='color:red;font-family:arial'> Warning(s) (<img src='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSvv9YYqFZSx-lvU8ws56OSVIdZ7R1BI4rOqQ&usqp=CAU' width=10></img>) </style> and "+ count_0 +  "<style='color:blue;font-family:arial'> Suggestion(s) (<img src='https://upload.wikimedia.org/wikipedia/commons/thumb/2/25/Info_icon-72a7cf.svg/1200px-Info_icon-72a7cf.svg.png' width=10></img>)</style> identified.</b>"
        st.components.v1.html(war_count_str, height=30, scrolling=False)
        if len(analysis_df) > 0:
            st.write(analysis_df[['ALERT_TYPE','MEDICINENAME','ALERT_CATEGORY','ALERT_MESSAGE']].sort_values(by=['ALERT_TYPE','MEDICINENAME']).to_html(escape=False, index=False), unsafe_allow_html=True)


    #Submit prescription
    if submit_pres_button:
        now = datetime.now()
        #st.dataframe(analysis_df)
        #Create log records
        if len(analysis_df)>0:
            alerted_medicines = list(analysis_df['MEDICINENAME'])
            for x in range(len(medicine_df)):
                if medicine_df['MEDICINENAME'][x] not in alerted_medicines:
                    analysis_df = analysis_df.append(dict(zip(analysis_df.columns,[medicine_df['MEDICINENAME'][x], "None", "","" ,0])), ignore_index = True)
            analysis_df['IP']=pres_IP
            analysis_df['userID'] = user.split(" (")[0]
            analysis_df['page'] = "Prescription"
            analysis_df['date'] = now.strftime("%d/%m/%Y")
            analysis_df['time'] = now.strftime("%H:%M:%S")
            analysis_df['ward'] = ward
            dash_df = dash_df.append(analysis_df[['IP','MEDICINENAME','ALERT_CATEGORY','Flag','userID','page','date','time','ward']], ignore_index = True)
            dash_df.to_csv(path+ "/data/dashboard.csv", index = False)
        else:

            analysis_df['MEDICINENAME'] = medicine_df['MEDICINENAME']
            analysis_df['IP']=pres_IP
            #analysis_df['GENERICNAME'] = medicine_df['GENERICNAME']
            analysis_df['ALERT_CATEGORY'] = "None"
            analysis_df['ALERT_MESSAGE'] = ""
            analysis_df['ALERT_TYPE']=""
            analysis_df['Flag']=0
            analysis_df['userID'] = user.split(" (")[0]
            analysis_df['page'] = "Prescription"
            analysis_df['date'] = now.strftime("%d/%m/%Y")
            analysis_df['time'] = now.strftime("%H:%M:%S")
            analysis_df['ward'] = ward
            dash_df = dash_df.append(analysis_df[['IP','MEDICINENAME','ALERT_CATEGORY','Flag','userID','page','date','time','ward']], ignore_index = True)
            dash_df.to_csv(path+ "/data/dashboard.csv", index = False)    
        st.info("Identified alert(s) were overriden. Prescription was submitted successfully.")

##### INDENT DSS PAGE

if page == "Indent DSS": 

    #Input from user
    # ~~~~~~~~~~~~~~
	
    
    #Title
    st.write("<h2><center> Indent Decision Support System </center></h2>", unsafe_allow_html=True)
    

    ind_IP = st.text_input("Enter In-Patient number: ('IDxxxxxx')")
    audit_ind_button=0
    submit_ind_button=0
    ward=""
    pres_med=[]
    
    #Check if IP entered
    if len(ind_IP) > 0:
        
        
        new_entry = 0
        Dates =[]
        IP_df = indent_df[indent_df['IPNUMBER'] == str(ind_IP)][['CREATEDDATE','DRUGCODE','MEDICINENAME','MedicineType','Corrected_GenericNames','WARDNAME']].sort_values(by='CREATEDDATE', ascending=False )
        if len(IP_df['CREATEDDATE'].unique())>3:
            Dates = IP_df['CREATEDDATE'].unique()[:3]
            IP_df = IP_df[IP_df['CREATEDDATE'].isin(Dates)]
        elif len(IP_df['CREATEDDATE'].unique())>0:
            Dates = IP_df['CREATEDDATE'].unique()
            IP_df = IP_df[IP_df['CREATEDDATE'].isin(Dates)]
        else:
            new_entry = 1
            
        #Dislay recent prescritions    
        st.sidebar.subheader("Recent Prescriptions: " +ind_IP)
        #st.sidebar.title("Patient History")
        #st.sidebar.subheader("Recent Prescription Summary:")
        all_wards = list(indent_df['WARDNAME'].unique())
        default_index=0
        if new_entry: 
            #st.write("New")
            st.sidebar.write("None")
        else:
            past_unique_gen_names = IP_df['Corrected_GenericNames'].unique()
            history_df = IP_df[['CREATEDDATE','MEDICINENAME']].set_index('CREATEDDATE')
            st.sidebar.dataframe(history_df['MEDICINENAME'])
                   
            current_ward = IP_df['WARDNAME'].tolist()[0].strip()
            default_index = all_wards.index(current_ward)
            
        #Select default ward from historical data    
        ward = st.selectbox("Choose current ward :", all_wards,index = default_index)

        #Enter medicines for prescription
        pres_med = st.multiselect("Enter all medicine names :", list(drug_df['MEDICINENAME'].unique()),[])
        st.write("<br>",unsafe_allow_html=True)
        
        #Button click action
        dummy1,dummy2,dummy3 = st.beta_columns(3)
        with dummy1:
            audit_ind_button = st.button("Audit Indents")
            
        with dummy3:
            submit_ind_button = st.button("Submit Indents")
    else:
        st.error("Please enter IP number to proceed.")
   
    #-------------------------------------------------------------------------------------------------------------
    #Data analysis
    #~~~~~~~~~~~~~~
 
    count_1 = count_0 = str(0)
    if len(pres_med)>0:
        
        medicine_df = pd.DataFrame(columns= medicine_df.columns)
        analysis_df = pd.DataFrame(columns= analysis_df.columns)
        
        #pres_med = [x.strip() for x in pres_med]
        medicine_df['MEDICINENAME']= pres_med
        #st.write(medicine_df)
        for x in range(len(medicine_df)):
            generic_name = drug_df['Corrected_GenericNames'][drug_df['MEDICINENAME'] == medicine_df['MEDICINENAME'][x]].values[0]
            #st.write(medicine_df['MEDICINENAME'][x])
            #st.write(x, generic_name)
            medicine_df['GENERICNAME'][x] = generic_name
 
        
            #Missing drugs------------------------------
            if len(biz_rules_apriori_df[biz_rules_apriori_df['itemsets'].str.contains(generic_name)].sort_values(by = 'support', ascending = False).head(10)) > 0:
                apriori_list = biz_rules_apriori_df[biz_rules_apriori_df['itemsets'].str.contains(generic_name)].sort_values('support', ascending = False)['itemsets'].head(10).values
                #st.write(list(apriori_list))
                flattened_apriori_list = flatten_list(apriori_list, generic_name)
                if len(flattened_apriori_list) > 0 :
                    medicine_df['Missingdrug_flag'][x]=1
                    medicine_df['MissingDrugs'][x] = flattened_apriori_list
                    #st.write(flattened_apriori_list)
                else:
                    medicine_df['Missingdrug_flag'][x]=0
                    medicine_df['MissingDrugs'][x]=""
        
            
            else:
                medicine_df['Missingdrug_flag'][x]=0
                medicine_df['MissingDrugs'][x]=""
            #Missing drugs---------------------------------    
    
    
        existing_gen_names = list(medicine_df['GENERICNAME'])
        
    
        #Therapeutic duplication/overdose-----------------------------
        flat_gen_name_df = pd.DataFrame(columns = ['index','medicine_name','original_gen','flat_gen'])
        #Flatten list
        #dupes = [n, x for n, x in enumerate(existing_gen_names) if x in existing_gen_names[:n]]
        for x in range(len(existing_gen_names)):
            if existing_gen_names[x].find('+') > -1:
                temp = existing_gen_names[x].split("+")
                temp = [i.strip() for i in temp]
                for item in temp:
                    dup_record = [x,medicine_df['MEDICINENAME'][x],existing_gen_names[x],item]
                    flat_gen_name_df = flat_gen_name_df.append(dict(zip(flat_gen_name_df.columns, dup_record)), ignore_index = True)
            else:
                item= existing_gen_names[x].strip()
                dup_record = [x,medicine_df['MEDICINENAME'][x],existing_gen_names[x],item]
                flat_gen_name_df = flat_gen_name_df.append(dict(zip(flat_gen_name_df.columns, dup_record)), ignore_index = True)
        duplicate_gen_names = list(set(flat_gen_name_df['flat_gen'][flat_gen_name_df.duplicated('flat_gen')]))
        duplicates_df = flat_gen_name_df[flat_gen_name_df['flat_gen'].isin(duplicate_gen_names)]
        #drop_duplicates_df = duplicates_df.drop_duplicates(subset='flat_gen', keep='first')
        exact_gen_duplicates = duplicates_df[duplicates_df.duplicated('original_gen')]  #Overdose
        #st.dataframe(exact_gen_duplicates)
        if len(exact_gen_duplicates) > 0:
            for row in exact_gen_duplicates.iterrows():
                #st.write(row[1]['flat_gen'])
                overdose_alert_text = row[1]['flat_gen'] + " has been prescribed more than once. Please check dosage."
                overdose_alert = [row[1]['medicine_name'],'Drug overdose',overdose_alert_text,1,1]
                analysis_df = analysis_df.append(dict(zip(analysis_df.columns, overdose_alert)), ignore_index = True)
        subset_gen_name_duplicates = pd.concat([duplicates_df,exact_gen_duplicates]).drop_duplicates(keep=False) #Therapeutic duplication
        #st.dataframe(subset_gen_name_duplicates)
        if len(subset_gen_name_duplicates ) > 0:
            for row in subset_gen_name_duplicates .iterrows():
                #st.write(row[1]['flat_gen'])
                ther_dup_alert_text = row[1]['flat_gen'] + " has being found in the composition of another medicine also."
                ther_dup_alert = [row[1]['medicine_name'],'Therapeutic duplication',ther_dup_alert_text,1,1]
                analysis_df = analysis_df.append(dict(zip(analysis_df.columns, ther_dup_alert)), ignore_index = True)
        exact_medicine_duplicates=exact_gen_duplicates[exact_gen_duplicates.duplicated('medicine_name')] #Drug continuity 
        #st.dataframe(flat_gen_name_df )
        #st.dataframe(duplicates_df)
        #st.dataframe(exact_gen_duplicates)
        #st.dataframe(subset_gen_name_duplicates)
        #Therapeutic duplication/overdose-----------------------------
    
        for x in range(len(medicine_df)):
           
            #Missing drugs--------------------------
            #Check for existing drugs against the missing drug list and update the missing drugs list.
            if medicine_df['Missingdrug_flag'][x] == 1:
                updated_missing_drug_list.extend(list(set(medicine_df['MissingDrugs'][x]) - set(existing_gen_names)))
                medicine_df['Missingdrug_flag'][x]=0
                medicine_df['MissingDrugs'][x]=""
            #Missing drugs--------------------------    
        
  
        #Drug Interaction----------------------- 
        unique_generic_names = list(set(existing_gen_names))
        DI_check_list = []
        DI_list =[]
        for gen_name in unique_generic_names:
            flag_drug=[row[1] for index, row in biz_rules_DI_df.iterrows() if gen_name.find(row[0]) > -1]
            if len(flag_drug) > 0:
                DI_check_list.append([gen_name, flag_drug])
        #st.write(DI_check_list)        
        for item in DI_check_list:
            excluded_genlist = unique_generic_names
            excluded_genlist.remove(item[0])
            for gen_name in excluded_genlist:
                DI_gen_name = [[gen_name, DI_item] for DI_item in item[1] if gen_name.find(DI_item) > -1]
                if len(DI_gen_name) >0:
                    DI_list.append([item[0], DI_gen_name])           
        
        #st.write(DI_list)
        for DI_item in DI_list:
            Med2 = Med1 = DI_Med1 = DI_Med2 = ""
            Med1_list= Med2_list=[]
            Med1_list=list(medicine_df['MEDICINENAME'][medicine_df['GENERICNAME']== DI_item[0]].values)
            Med1 = ", ".join(Med1_list)
            DI_Med1 = DI_item[0]
            #st.write(DI_item[1])
            if len(DI_item[1])>1:
                for item in DI_item[1]:
                    temp_med = list(medicine_df['MEDICINENAME'][medicine_df['GENERICNAME']== item[0]].values)
                    #st.write("in")
                    Med2_list.append(temp_med)
                    #st.write(Med2_list)
                    Med2 = ", ".join(Med2_list)
                    DI_Med2 = DI_Med2 + item[0] + " "
            else:
                Med2_list = list(medicine_df['MEDICINENAME'][medicine_df['GENERICNAME']== DI_item[1][0][0]].values)
                Med2 = ", ".join(Med2_list)
                #st.write(Med2)
                DI_Med2 = DI_item[1][0][0]
            #st.write("Cannot prescribe " +  Med1 + " along with " + Med2+ " due to "+ DI_Med1 +" - "+ DI_Med2 +" interaction.")
            DI_alert_text = "SHOULD NOT prescribe " +  Med1 + " along with " + Med2+ " due to "+ DI_Med1 +" - "+ DI_Med2 +" interaction."
            DI_alert_record = [Med1_list[0], "Drug Interaction", DI_alert_text, 1,1]
            analysis_df = analysis_df.append(dict(zip(analysis_df.columns, DI_alert_record)), ignore_index = True)
                         
        #Drug Interaction----------------------- 
        
        #Historical Drug Interaction----------------------- 
        hist_unique_gen_names = list(IP_df['Corrected_GenericNames'].unique())
        hist_DI_check_list = []
        hist_DI_list =[]
        hist_flag_drug=[]
        #st.write(hist_unique_gen_names)
        for item in DI_check_list:
            #st.write(item)
            for hist_item in hist_unique_gen_names:
                #st.write(", ".join(item[1]),hist_item)
                if (", ".join(item[1])).find(hist_item)> -1:
                    #st.write("YES")
                    hist_med2 = IP_df['MEDICINENAME'][IP_df['Corrected_GenericNames']==hist_item].values[0]
                    curr_med1 = medicine_df['MEDICINENAME'][medicine_df['GENERICNAME']==item[0]].values[0]
                    hist_DI_alert_text = "CANNOT prescribe "+curr_med1+" unless "+hist_med2+" prescribed earlier is discontinued. "+item[0] +" - "+ hist_item +" interaction is harmful."
                    hist_DI_alert_record = [curr_med1, "Drug Interaction", hist_DI_alert_text,1,1]
                    analysis_df = analysis_df.append(dict(zip(analysis_df.columns, hist_DI_alert_record)), ignore_index = True)
                    
        #Historical Drug Interaction----------------------- 
        
        #Historical Therapeutic duplication/overdose-----------------------------
        drug_repetition = list(set(unique_generic_names) & set(hist_unique_gen_names))
        if len(drug_repetition)>0:
            for item in drug_repetition:
                hist_med2 = IP_df['MEDICINENAME'][IP_df['Corrected_GenericNames']==item].values[0]
                curr_med1 = medicine_df['MEDICINENAME'][medicine_df['GENERICNAME']==item].values[0]
                if hist_med2 != curr_med1:
                    hist_ther_dup_alert_text = item + " has being found in the composition of recently prescribed "+hist_med2+" also. Reconsider dosage if latter is not discontinued."
                    hist_DI_alert_record = [curr_med1, "Therapeutic duplication", hist_ther_dup_alert_text,1,1]
                    #st.write(hist_DI_alert_record)
                    analysis_df = analysis_df.append(dict(zip(analysis_df.columns, hist_DI_alert_record)), ignore_index = True)
        
        
        #Historical Therapeutic duplication/overdose-----------------------------
        
        #Missing drugs -----------------        
        updated_missing_drug_list = list(set(updated_missing_drug_list))
        medicine_df['MissingDrugs'][0] = ", ".join(updated_missing_drug_list[:3])
    
        if len(updated_missing_drug_list) > 0: 
            medicine_df['Missingdrug_flag'][0]=1
        
        if medicine_df['Missingdrug_flag'][0] == 1:
            #st.write("<br>",unsafe_allow_html=True)
            ###-> Convert to list type display
            html_str = "<img src='https://upload.wikimedia.org/wikipedia/commons/f/f6/Lol_question_mark.png' width=25></img><b> &nbsp Did you forget indenting the following?</b> <br> "
            #st.components.v1.html(html_str, height=40, scrolling=False)
            loop = 1
            for item in medicine_df['MissingDrugs'][0].split(","):
                #st.write(str(loop)+". "+item.strip())
                loop +=1
        #Missing drugs ------------------
 
        st.write("<br>",unsafe_allow_html=True)
        
        if len(analysis_df)>0:
            count_1 = str(len(analysis_df[analysis_df['Flag']==1]))
            count_0 = str(len(analysis_df[analysis_df['Flag']==0]))
            
    
        for x in range(len(analysis_df)):
            #st.write(analysis_df)
            analysis_df['ALERT_TYPE'][x] = set_flag(int(analysis_df['ALERT_TYPE'][x]))
        

        
    elif len(pres_IP) > 0 & len(pres_med) < 1 :
        st.error("Please enter medicine names.")
    else: pass
 
    #Display analysis results
    if audit_ind_button:
      
        if len(medicine_df) > 0:
            st.write("Your prescription summary:")  
            st.write(medicine_df[['MEDICINENAME','GENERICNAME']].to_html(escape=False, index=False), unsafe_allow_html=True)
            #st.write("<br>",unsafe_allow_html=True)
        if len(analysis_df) > 0:
            if medicine_df['Missingdrug_flag'][0] == 1:
                st.write("<br>",unsafe_allow_html=True)
                
                html_str = "<img src='https://upload.wikimedia.org/wikipedia/commons/f/f6/Lol_question_mark.png' width=20></img><b> &nbsp Did you forget indenting any of the following?</b> <br> "
                st.components.v1.html(html_str, height=40, scrolling=False)
                loop = 1
                for item in medicine_df['MissingDrugs'][0].split(","):
                    st.write(str(loop)+". "+item.strip())
                    loop +=1
        st.write("<br>",unsafe_allow_html=True)    
        war_count_str = "<b>"+ count_1 + "<style='color:red;font-family:arial'> Warning(s) (<img src='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSvv9YYqFZSx-lvU8ws56OSVIdZ7R1BI4rOqQ&usqp=CAU' width=10></img>) </style> and "+ count_0 +  "<style='color:blue;font-family:arial'> Suggestion(s) (<img src='https://upload.wikimedia.org/wikipedia/commons/thumb/2/25/Info_icon-72a7cf.svg/1200px-Info_icon-72a7cf.svg.png' width=10></img>)</style> identified.</b>"
        st.components.v1.html(war_count_str, height=30, scrolling=False)
        #st.write(medicine_df)
        if len(analysis_df) > 0:
            st.write(analysis_df[['ALERT_TYPE','MEDICINENAME','ALERT_CATEGORY','ALERT_MESSAGE']].sort_values(by=['ALERT_TYPE','MEDICINENAME']).to_html(escape=False, index=False), unsafe_allow_html=True)
            #st.dataframe(analysis_df)
    
    #Submit indents 
    if submit_ind_button:
        now = datetime.now()
        #st.dataframe(analysis_df)
        
        #Create log data
        if len(analysis_df)>0:
            alerted_medicines = list(analysis_df['MEDICINENAME'])
            for x in range(len(medicine_df)):
                if medicine_df['MEDICINENAME'][x] not in alerted_medicines:
                    analysis_df = analysis_df.append(dict(zip(analysis_df.columns,[medicine_df['MEDICINENAME'][x], "None", "","" ,0])), ignore_index = True)
            analysis_df['IP']=ind_IP
            analysis_df['userID'] = user.split(" (")[0]
            analysis_df['page'] = "Indent"
            analysis_df['date'] = now.strftime("%d/%m/%Y")
            analysis_df['time'] = now.strftime("%H:%M:%S")
            analysis_df['ward'] = ward
            dash_df = dash_df.append(analysis_df[['IP','MEDICINENAME','ALERT_CATEGORY','Flag','userID','page','date','time','ward']], ignore_index = True)
            dash_df.to_csv(path+ "/data/dashboard.csv", index = False)
        else:

            analysis_df['MEDICINENAME'] = medicine_df['MEDICINENAME']
            analysis_df['IP']=ind_IP
            #analysis_df['GENERICNAME'] = medicine_df['GENERICNAME']
            analysis_df['ALERT_CATEGORY'] = "None"
            analysis_df['ALERT_MESSAGE'] = ""
            analysis_df['ALERT_TYPE']=""
            analysis_df['Flag']=0
            analysis_df['userID'] = user.split(" (")[0]
            analysis_df['page'] = "Indent"
            analysis_df['date'] = now.strftime("%d/%m/%Y")
            analysis_df['time'] = now.strftime("%H:%M:%S")
            analysis_df['ward'] = ward
            dash_df = dash_df.append(analysis_df[['IP','MEDICINENAME','ALERT_CATEGORY','Flag','userID','page','date','time','ward']], ignore_index = True)
            dash_df.to_csv(path+ "/data/dashboard.csv", index = False)
        st.info("Identified alert(s) were overriden. Indents were submitted successfully.")
                


    
if page == "Dashboard":

    #Download log data - file generation
    def get_table_download_link(df,data_type,date):
        #"""Generates a link allowing the data in a given panda dataframe to be downloaded in:  dataframe out: href string """
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
        file_name = data_type + "_Log Data_"+str(date)+"_"+str(end_date)
        href = f'<center><a href="data:file/csv;base64,{b64}"><input type="button" value="DOWNLOAD {file_name}.csv"></a></center>'
        return href
    load_data()
    
    import datetime as dt   
        
    #Provide dashbord controls for date and data source selection
    
    #"Warnings overridden over time"------------------------------------------------
    st.sidebar.title("Dashboard Controls")
    page_type = st.sidebar.selectbox("Select data source for analysis:",("Prescription","Indent"))
    format = 'MMM DD, YYYY'  # format output
    start_date = dt.date(year=2021,month=1,day=1)
    end_date = dt.datetime.now().date()
    max_days = end_date-start_date
    #slider = cols1.slider('Select date', min_value=start_date, value=end_date ,max_value=end_date, format=format)
    report_start_value = dash_df['date'].min().split("/")
    #st.write(report_start_value)
    report_start_value = dt.date(year=int(report_start_value[2]),month=int(report_start_value[1]),day=int(report_start_value[0]))
    start_time = st.sidebar.slider("Select start time for reports:",min_value=start_date, value=report_start_value,max_value=end_date, format=format)  #REphrase text
    log_count = 0
    log_download_df = dash_df[dash_df['page'] == page_type]
    #st.write(dash_df['date'].max(),str(report_start_value))
    date_filter = str(str(start_time).split("-")[2])+"/"+str(str(start_time).split("-")[1])+"/"+str(str(start_time).split("-")[0])
    if log_download_df['date'].max() >= date_filter:
        log_download_df = log_download_df[log_download_df['date'] >= date_filter]
        log_count = len(log_download_df)
    st.sidebar.info("Total "+ str(log_count)+" log record(s) found.")
    
    #Title on run-time
    if page_type == "Prescription":
        st.write("<h2><center> Prescription DSS Dashboard </center></h2>", unsafe_allow_html=True)
        #left,center, right = st.beta_columns(3)
        #with center:
        
    else:
        st.write("<h2><center> Indent DSS Dashboard </center></h2>", unsafe_allow_html=True)
    
    #Graph generation on fitered data
    if log_count>0:

        overriden_df_1 = log_download_df.pivot_table(index='date', aggfunc= {'Flag': 'sum', 'MEDICINENAME' : 'count'})
        overriden_df_1.rename(columns = {"Flag":"Errors overriden", 'MEDICINENAME':'Total Medicines prescribed'}, inplace = True)
        st.subheader("Alerts Overridden over Time")
        #pd.to_datetime(df['closingDate'], format='%dd-%mmm-%yy')
        overriden_df_1.reset_index(inplace=True)
        overriden_df_1['date'] = [(datetime.strptime(date_item, '%d/%m/%Y').date()).strftime('%d %b,%y') for date_item in overriden_df_1['date']]
        overriden_df_1 = overriden_df_1.set_index('date')
        #date_item = '17/06/2021'
        #st.write((datetime.strptime(date_item, '%d/%m/%Y').date()).strftime('%d %b,%Y'))
        #st.write(overriden_df_1.sort_values(by = 'date'))
        st.line_chart(overriden_df_1)
        #"Warnings overridden over time"------------------------------------------------
        
        #Alerts overriden by wards---------------------------------------------
        st.subheader("Alerts Overriden by Wards")
        ward_type = st.multiselect("Select ward type:",(biz_rules_ward_df['Category'].unique()),[])
        #st.write(ward_type)  
        if len(ward_type)>0:
            #st.write(ward_type)
            wards_list = biz_rules_ward_df['Wards'][biz_rules_ward_df['Category'].isin(ward_type)]
            #st.write(wards_list)
            overriden_df_5 = log_download_df[log_download_df['ward'].isin(wards_list)].pivot_table(index=['ward'], aggfunc= {'Flag' : 'sum'})
            overriden_df_5.rename(columns = {'Flag': "Errors overriden"}, inplace = True)
            st.bar_chart(overriden_df_5)
        
        #Alerts overriden by wards---------------------------------------------
        
        #"Alert categories overriden"------------------------------------------------
        overriden_df_2 = log_download_df.pivot_table(index='ALERT_CATEGORY',aggfunc= {'Flag': 'sum', 'MEDICINENAME' : 'count'})
        #overriden_df_2.reset_index(inplace = True)
        overriden_df_2.rename(columns = {'Flag': "Errors overriden",'MEDICINENAME':'Total Medicines prescribed'}, inplace = True)
        #st.dataframe(overriden_df_2)
        
        
        st.subheader("Alerts Overriden by Categories")
        st.bar_chart(overriden_df_2[['Total Medicines prescribed','Errors overriden']])
           
        #"Alert categories overriden"------------------------------------------------
        
        
        #Alert categories overriden by page---------------------------------------------
        
        overriden_df_3 = log_download_df.pivot_table(index=['ALERT_CATEGORY'], aggfunc= {'page' : 'count'})
        overriden_df_3.rename(columns = {'page': 'Count'}, inplace = True)
        overriden_df_3.fillna(0, inplace = True)
        #with right:
        st.sidebar.subheader("Summary of Alert Overrides")
        st.sidebar.dataframe(overriden_df_3.astype('int32').style.highlight_max(color='darkorange', axis=0))
        
        #Alert categories overriden by page---------------------------------------------
        
        #Alerts overriden by user---------------------------------------------
        overriden_df_4 = log_download_df.pivot_table(index=['userID'], aggfunc= {'Flag' : 'sum'})
        overriden_df_4.rename(columns = {'Flag': "Count"}, inplace = True)
        st.sidebar.subheader("Alert Overrides by Users")
        st.sidebar.dataframe(overriden_df_4.astype('int32').sort_values(by='Count', ascending=False).style.highlight_max(color='darkorange', axis=0))
        #Alerts overriden by user---------------------------------------------
        
        #Download option for log data
        st.markdown(get_table_download_link(log_download_df,page_type,str(start_time)), unsafe_allow_html=True)
    else:
        st.info("Please choose a different date range for reports.")
    
    #