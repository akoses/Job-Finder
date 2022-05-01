import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from bs4 import BeautifulSoup


indeed = pd.read_csv("indeed_jobs.csv")
linkedin = pd.read_csv("linkedin_jobs.csv")


def map_description(description):
    
    soup = BeautifulSoup(description, "html.parser")
    
    results_li = soup.find_all('li')
    results_p = soup.find_all('p')
    
    results_li = [result.get_text() for result in results_li]
    results_p = [result.get_text() for result in results_p]
    length = 0

    if len(results_li) == 0 and len(results_p) == 0:
        print('ZERO')
        return 0
    
    for result in results_li:
        length += len(result.split())
    
    for result in results_p:
        length += len(result.split())
    
    return length


y_indeed = indeed['description']
y_linkedin = linkedin['description']

max_seq_indeed = 512
max_seq_linkedin = 512


y_linkedin = y_linkedin.apply(map_description)
y_indeed = y_indeed.apply(map_description)

print(y_indeed.mean(), y_indeed.max(), y_indeed.min(), y_indeed.count())

print(y_linkedin.mean(), y_linkedin.max(), y_linkedin.min(), y_linkedin.count())

sns.distplot(y_indeed, hist=True, kde=True, color='r',label='Indeed')
sns.distplot(y_linkedin, hist=True, kde=True, color='b', label='LinkedIn')

plt.axvline(max_seq_indeed, color='r', linestyle='--')
plt.axvline(max_seq_linkedin, color='b', linestyle='--')
plt.xlabel('Number of words in description')
plt.ylabel('Frequency')
plt.title('Distribution of number of words in description')
plt.legend()
plt.show()
