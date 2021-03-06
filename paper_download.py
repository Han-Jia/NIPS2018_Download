# Crawl JMLR Paper Abstract
from urllib.request import urlopen
import time
from bs4 import BeautifulSoup
import pickle
from PyPDF2 import PdfFileMerger
import zipfile
import os
from tqdm import tqdm
import wget
import shutil

init_url = 'http://papers.nips.cc/book/advances-in-neural-information-processing-systems-31-2018'
# create current dict
title_list = []
paper_dict = dict()

if os.path.exists('init_url.dat'):
    with open('init_url.dat', 'rb') as f:
        content = pickle.load(f)
else:
    content = urlopen(init_url).read()
    with open('init_url.dat', 'wb') as f:
        pickle.dump(content, f)
        
soup = BeautifulSoup(content, 'html.parser')
temp_soup = soup.find_all('ul')[1]   # after the book section
paper_list = temp_soup.find_all('li')
error_log = []
# num_download = 5 # number of papers to download
num_download = len(paper_list)

# make temp dir to unzip zip file
temp_zip_dir = './temp_zip'
if not os.path.exists(temp_zip_dir):
    os.mkdir(temp_zip_dir)  
else:
    # remove all files
    for unzip_file in os.listdir(temp_zip_dir):
        if os.path.isfile(os.path.join(temp_zip_dir, unzip_file)):
            os.remove(os.path.join(temp_zip_dir, unzip_file))
        if os.path.isdir(os.path.join(temp_zip_dir, unzip_file)):
            shutil.rmtree(os.path.join(temp_zip_dir, unzip_file))
        else:
            print('Cannot Remove - ' + os.path.join(temp_zip_dir, unzip_file))  
        
if os.path.exists('main.pdf'):
    os.remove('main.pdf')
    
if os.path.exists('supp.pdf'):
    os.remove('supp.pdf')
        
if os.path.exists('supp.zip'):
    os.remove('supp.zip')
            
# parse each paper
for p in tqdm(zip(paper_list, range(num_download))):
    # get title
    print('\n')
    p = p[0]
    title = p.a.text
    try:
        print(title)
    except:
        print(title.encode('utf8'))
        
    if ':' in title:
        title = title.replace(':', ' - ')
    title = "".join(i for i in title if i not in "\/:*?<>|")
    title_list.append(title)
    # get abstract page url
    url2 = p.a.get('href')
    
    if os.path.exists(title + '.pdf'):
        continue
    
    # try 3 times
    success_flag = False
    for _ in range(3):
        try:
            abs_content = urlopen('http://papers.nips.cc'+url2, timeout=20).read()
            soup_temp = BeautifulSoup(abs_content, 'html.parser')
            abstract = soup_temp.find('p',{'class':'abstract'}).text.strip()
            paper_dict[title] = abstract
            
            paper_link = soup_temp.findAll('a')[4].get('href')
            supp_link = soup_temp.findAll('a')[6].get('href')
            supp_type = supp_link.split('.')[-1]
            
            # download paper
            filename = wget.download('http://papers.nips.cc' + paper_link, 'main.pdf')
            #req = urlopen('http://papers.nips.cc' + paper_link, None, 20)
            #with open('main.pdf', 'wb') as fp:
                #fp.write(req.read())
            
            # download supp
            supp_succ_download = False
            try:
                supp_filename = wget.download('http://papers.nips.cc' + supp_link, 'supp.' + supp_type)
                #req = urlopen('http://papers.nips.cc' + supp_link, None, 20)
                supp_succ_download = True
                no_supp = False
            except Exception as e:
                no_supp = e.code == 404
                
            if not no_supp and supp_succ_download:
                #with open('supp.' + supp_type, 'wb') as fp:
                    #fp.write(req.read())            
                
                # if zip file, unzip and extrac pdf file
                if supp_type == 'zip':
                    zip_ref = zipfile.ZipFile('supp.zip', 'r')
                    zip_ref.extractall(temp_zip_dir)
                    zip_ref.close()    
                    
                    # find if there is a pdf file (by listing all files in the dir)
                    supp_pdf_list = [os.path.join(dp, f) for dp, dn, filenames in os.walk(temp_zip_dir) for f in filenames if f.endswith('pdf')]
                    # rename the first pdf file
                    if len(supp_pdf_list) == 0:
                        supp_pdf_path = None
                    else:
                        # by default, we only deal with the first pdf
                        os.rename(supp_pdf_list[0], './supp.pdf')
                        supp_pdf_path = './supp.pdf'
                        
                    # empty the temp_folder (both the dirs and files)
                    for unzip_file in os.listdir(temp_zip_dir):
                        if os.path.isfile(os.path.join(temp_zip_dir, unzip_file)):
                            os.remove(os.path.join(temp_zip_dir, unzip_file))
                        if os.path.isdir(os.path.join(temp_zip_dir, unzip_file)):
                            shutil.rmtree(os.path.join(temp_zip_dir, unzip_file))
                        else:
                            print('Cannot Remove - ' + os.path.join(temp_zip_dir, unzip_file))
                    
                    if supp_pdf_path is None:
                        if os.path.exists('supp.zip'):
                            os.remove('supp.zip')                              
                        os.rename('./main.pdf', title + '.pdf')
                        success_flag = True
                        break
                            
                elif supp_type.lower() == 'pdf':
                    supp_pdf_path = 'supp.' + supp_type
                    
                
                # combine two pdfs into one file
                merger = PdfFileMerger()
                f_handle1 = open('main.pdf', 'rb')
                merger.append(f_handle1)
                f_handle2 = open(supp_pdf_path, 'rb')
                merger.append(f_handle2)
                    
                with open(title + '.pdf', 'wb') as fout:
                    merger.write(fout)
                    
                f_handle1.close()
                f_handle2.close()
                merger.close()
                # remove main.pdf and supp.pdf
                os.remove('main.pdf')
                os.remove(supp_pdf_path)
                os.remove('supp.zip')
            elif no_supp:
                # rename the main.pdf with title
                os.rename('./main.pdf', title + '.pdf')
            else:
                # download supp error
                time.sleep(20)
                if os.path.exists('main.pdf'):
                    os.remove('main.pdf')   
                if os.path.exists(supp_pdf_path):
                    os.remove(supp_pdf_path)
                if os.path.exists('supp.zip'):
                    os.remove('supp.zip')                
                continue
            
            success_flag = True
            break
        except:
            time.sleep(5)
            continue

    if not success_flag:
        paper_dict[title] = '\n'       
        error_log.append((title, 'http://papers.nips.cc'+url2))
        print('ERROR: ' + title)

# store the results
# 1. store in the pickle file
with open('NIPS2018_pre.dat','wb') as f:
    pickle.dump(paper_dict, f)

# 2. write error log
print('write error log')
with open('download_err_log.txt', 'w') as f:
    for log in tqdm(error_log):
        for e in log:
            f.write(e)
            f.write('\n')
    
        f.write('\n')