import pandas as pd
import streamlit as st
from tabulate import tabulate
import sys
import datetime as dt
import time
from bs4 import BeautifulSoup
import requests

# scrapes ownership info from finintel
def stockOwnership(ticker):    
    url = 'https://fintel.io/so/us/' + ticker
    html = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(html.text, 'lxml')
    
    # finds specific div with tables
    match = soup.find('div', class_="stock-page")
    
    # pd.set_option("display.max_rows", 999) #sets 
    filing_lst = []
    
    # trys to find the 13D filings and appends to filing_lst
    try:
        html_13D = match.find('p', text='13D/G Filings').text
        filing_lst.append(html_13D)
    except:
        pass 
    # trys to find the 13F filings and appends to filing_lst
    try:
        html_13F = match.find('p', text='13F and Fund Filings').text
        filing_lst.append(html_13F)
    except:
        pass
    
    if len(filing_lst) == 2:
        # pandas looks for tables in the html and puts them in list format
        df = pd.read_html(html.text)
        # selects columns, drops NaN, sorts date, only keeps rows that are not 0, formats integers to have commas
        df_13D = df[1][['File Date', 'Form', 'Security', 'CurrentShares']].dropna().sort_values(by='File Date', ascending=False)
        df_13D = df_13D[(df_13D !=0).all(1)]
        df_13D['CurrentShares'] = df_13D['CurrentShares'].astype(int).map('{:,}'.format)
        # selects columns, drops NaN, sorts date, only keeps rows that are not 0, formats integers to have commas
        df_13F = df[2][['File Date', 'Form', 'Investor', 'Shares']].dropna().sort_values(by='File Date', ascending=False)
        df_13F = df_13F[(df_13F !=0).all(1)]
        df_13F['Shares'] = df_13F['Shares'].astype(int).map('{:,}'.format)
        
        df_13D.set_index('File Date', inplace=True)
        df_13F.set_index('File Date', inplace=True)
        
        st.header("13D/G Filings")
        st.dataframe(df_13D)
        st.header("13F Filings")
        if df_13F.empty == False:
            st.dataframe(df_13F)
        elif df_13F.empty == True:
            st.warning("No Filings Found")      
        
    elif len(filing_lst) == 1 and filing_lst[0] == '13D/G Filings':
        # pandas looks for tables in the html and puts them in list format
        df = pd.read_html(html.text)
        # selects columns, drops NaN, sorts date, only keeps rows that are not 0, formats integers to have commas
        df_13D = df[1][['File Date', 'Form', 'Security', 'CurrentShares']].dropna().sort_values(by='File Date', ascending=False)
        df_13D = df_13D[(df_13D !=0).all(1)]
        df_13D['CurrentShares'] = df_13D['CurrentShares'].astype(int).map('{:,}'.format)
        
        st.header("13D/G Filings")
        st.dataframe(df_13D)
        st.header("13F Filings")
        st.warning("No Filings Found")
        
    elif len(filing_lst) == 1 and filing_lst[0] == '13F and Fund Filings':
        df = pd.read_html(html.text)
        # selects columns, drops NaN, sorts date, only keeps rows that are not 0, formats integers to have commas
        df_13F = df[1][['File Date', 'Form', 'Investor', 'Shares']].dropna().sort_values(by='File Date', ascending=False)
        df_13F = df_13F[(df_13F !=0).all(1)]
        df_13F['Shares'] = df_13F['Shares'].astype(int).map('{:,}'.format)        
        
        st.header("13D/G Filings")
        st.warning("No filings found")
        st.header("13F Filings")
        st.dataframe(df_13F)
    
    elif len(filing_lst) == 0:
        st.header("13D/G Filings")
        st.warning("No filings found")
        st.header("13F Filings")
        st.warning("No filings found")
# scrapes catalyst info from biopharm     
def stockBio(ticker):
    url = 'https://www.biopharmcatalyst.com/company/' + ticker + '#drug-information'
    html = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(html.text, 'lxml')
    
    # finds div with class drug-info
    match = soup.find('div', class_="drug-info")
    
    names = []
    cnotes = []
    
    while True:
        try:
            # appends drug name to list
            for n in match.find_all("div", class_="drug-info__name"):
                names.append(n.text)
            # appends catalyst notes to list
            for c in match.find_all('div', class_='catalyst-note'):
                cnotes.append(c.text)
            # throws both lists into a single dataframe
            df_bio = pd.DataFrame(list(zip(names, cnotes)), columns = ['Name', 'Catalyst Notes'])
              
            st.table(df_bio)
            break
        except:
            st.warning("No bio-catalysts found")
            break               
# scrapes stock news from finviz
def stockNews(ticker):
    url = 'https://finviz.com/quote.ashx?t=' + ticker
    html = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(html.text, 'lxml')
    
    # finds news table within finviz website
    match = soup.find('table', class_="fullview-news-outer")
    
    st.markdown(match, unsafe_allow_html=True)
    
    # dates = []
    # dates1 = []
    # # appends dates in html to list
    # for d in match.find_all("td", width="130"):
    #     dates.append(d.text)
    # # splits the time away from date and appends to list
    # for d1 in dates:
    #     dates1.append(d1.split(' ')[0])       
    
    # titles = []
    # # appends new title to titles list
    # for t in match.find_all("a", class_="tab-link-news"):
    #     titles.append(t.text)

    # links = []
    # # appends link to links list
    # for h in match.find_all("a", class_="tab-link-news"):
    #     links.append(h.attrs['href'])
    # # outputs the most recent 20 news reports
    # for i in range(len(titles[:20])):
    #     st.write("{:>20}".format(dates[i]) + '\t' + titles[i])
# scrapes s-1 and s-3 fillings from sec edgar
def stockSec(ticker):
    url_1 = 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=' + ticker + '&type=s-3&dateb=&owner=exclude&count=100'
    url_2 = 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=' + ticker + '&type=s-1&dateb=&owner=exclude&count=100'

    html_1 = requests.get(url_1, headers={'User-Agent': 'Mozilla/5.0'})
    html_2 = requests.get(url_2, headers={'User-Agent': 'Mozilla/5.0'})
    df_s3 = pd.read_html(html_1.text)
    df_s1 = pd.read_html(html_2.text)

    # trys to look for s3 and s1 filings and prints response
    try:
        df_s3 = df_s3[2][['Filing Date', 'Filings']]            
    except IndexError and ValueError:
        df_s3 = pd.DataFrame()
        st.warning("No S-3 found") 
    try:
        df_s1 = df_s1[2][['Filing Date', 'Filings']]
    except IndexError and ValueError:
        df_s1 = pd.DataFrame()
        st.warning("No S-1 found") 
    
    # prints ouput based on which dataframes arn't empty or if both have elements       
    if len(df_s3) >= 1 and df_s1.empty == True:
        # print('***************** ' + stock +' S-3 Filing *****************', '\n')
        st.write(df_s3)
    elif len(df_s1) >= 1 and df_s3.empty == True:
        # print('***************** ' + stock +' S-1 Filing *****************', '\n')
        st.write(df_s1)
    elif len(df_s3) and len(df_s1) >= 1:
        df_sec = pd.concat([df_s3, df_s1]).sort_values(by=['Filing Date'], ascending=False)
        # print('***************** ' + stock +' S-3 & S-1 Filings *****************', '\n')
        st.write(df_sec)

st.markdown(
        f"""
<style>
    .reportview-container .main .block-container{{
        max-width: 50%;
    }}
</style>
""",
        unsafe_allow_html=True,
    )

ticker = st.text_input("Enter Ticker")

st.image('https://finviz.com/chart.ashx?t=' + ticker + '&ty=c&ta=1&p=d&s=l')

st.title("Stock Ownership")
stockOwnership(ticker)

st.title('S-1/S-3 Filings')
stockSec(ticker)

st.title("Bio Catalysts")
stockBio(ticker)

st.title('News')
stockNews(ticker)



