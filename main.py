import os
import sys
import re
import time
import ctypes
import subprocess
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup as bs

try:
	from scode.util import *
except ImportError:
	subprocess.run(['python', '-m', 'pip', 'install', '--upgrade', 'scode'])
	from scode.util import *

from scode.selenium import *

# ===============================================================================
#                               Definitions
# ===============================================================================
debug = True

driver = load_driver()
driver.set_page_load_timeout(10)
# driver.set_window_position(9999,9999)
# driver.minimize_window()

error_file_path = 'error.txt'
error_log_file_path = 'err_log.txt'

def find_tab_keyword(keyword_infos) :
	print('스마트 블록 탭 메뉴 데이터를 수집하겠습니다.')
	tab_data = {}
	last_keyword = ''
	len_keyword_infos = len(keyword_infos)
	for info_idx , info in enumerate(keyword_infos.items(),start=1) :
		try : 
			keyword_data = info[1]
			keyword = keyword_data[0]
			tab_keyword = keyword_data[1]
			blog_url = keyword_data[2].replace('blog.naver.com','m.blog.naver.com')
			search_url = f'https://m.search.naver.com/search.naver?sm=mtp_sly.hst&where=m&query={keyword}'
			menu = '#ct > section.sc.sp_intent_block._intent_block._pwr_root.intent_root_itb_bas._prs_itb_bas > div.api_subject_bx.__intent_popular_block__ > div > div.popular_header > a'
			tab_board = '#ct > section.sc.sp_intent_block._intent_block._pwr_root.intent_root_itb_bas._prs_itb_bas > div.api_ly_modal.__intent_popular_block_modal__ > div > div.modal_content._modal_scroller > div > div'
			
			if last_keyword != keyword :
				last_keyword = keyword
				driver.get(search_url)
				time.sleep(.2)
				try :
					driver.find_element(By.CSS_SELECTOR,menu).send_keys(Keys.ENTER)
				except NoSuchElementException :
					keyword_info = {info_idx : (keyword,tab_keyword,blog_url,'탭x')}
					tab_data.update(keyword_info)
					continue
				time.sleep(2)
				html = driver.page_source

			soup = bs(html, 'html.parser')
			tab_board = soup.select_one(tab_board)
			tab_menu_lst = tab_board.select('div.flick_bx')
			time.sleep(.1)



			for tab_key in tab_menu_lst :

				tab_link = tab_key.select_one('a').attrs['href']
				tab_title = tab_key.select_one('a > div > div.dsc_area > div.dsc').text
				if debug :print(f'{tab_title}\n{tab_link}')

				if tab_title == tab_keyword :
					keyword_info = {info_idx : (keyword,tab_keyword,blog_url,tab_link)}
					break

				keyword_info = {info_idx : (keyword,tab_keyword,blog_url,'탭x')}

				

			tab_data.update(keyword_info)
			print(f'{info_idx} / {len_keyword_infos} 번째 데이터 수집 완료', end='\r')

		except TimeoutError as e :
			timeour_err = f'{info_idx} 번째 데이터  - Timeout'
			err_string = f'error : {e}'
			print(f'{info_idx} 번째 데이터에서 시간 초과 오류 발생')
			input_data = {'reason' : err_string, 'data' : timeour_err }
			err_logging(input_data)
			fwrite(error_log_file_path,f'{keyword}\t{tab_keyword}\t{blog_url}')
			continue

		except Exception as e :
			err_string = f'error : {e}'
			print(err_string)
			input_data = {'reason' : err_string}
			err_logging(input_data)
	return tab_data

def run():
	
	input_file_path = 'input.txt'
	output1_file_path = 'output1.txt'
	output2_file_path = 'output2.txt'
	
	
	# Inintialize
	open(output1_file_path, 'w').close()
	open(output2_file_path, 'w').close()
	open(error_file_path, 'w').close()
	open(error_log_file_path, 'w').close()

	try:
		input_lst = [x.strip() for x in open(input_file_path).read().splitlines()]
	except UnicodeDecodeError:
		try:
			input_lst = [x.strip() for x in open(input_file_path, encoding='cp949').read().splitlines()]
		except UnicodeDecodeError:
			input_lst = [x.strip() for x in open(input_file_path, encoding='utf-8').read().splitlines()]

	while '' in input_lst :
		input_lst.remove('')

	

	
	total_cnt = len(input_lst)

	# TODO: 기능구현


	print('**'*10,'프로그램 시작','**'*10,'\n')
	print(f'{total_cnt} 개의 데이터 검사 합니다.')
	keyword_infos =  {}

	for idx,info in enumerate(input_lst,start=1) :
		try :
			keyword = info.split('\t')[0]
			tab_keyword = info.split('\t')[1]
			blog_url = info.split('\t')[2]

			keyword_info = {idx : (keyword,tab_keyword,blog_url)}
			keyword_infos.update(keyword_info)

		except IndexError :
			print('input.txt를 확인해주세요.')
			sys.exit()

		except Exception as e :
			err_string = f'error : {e}'
			print(err_string)
			input_data = {'reason' : err_string}
			err_logging(input_data)
	

	
	tab_data = find_tab_keyword(keyword_infos)

	print('\n')
	
	for idx, tab_info in tab_data.items() :
		try :
			if debug : print(tab_info)
			exist_flag = False
			keyword = tab_info[0]
			tab_keyword = tab_info[1]
			blog_url = tab_info[2]
			search_url = tab_info[3]

			if search_url == '탭x' :
				fwrite(output1_file_path,f'{keyword}\t{tab_keyword}\t{blog_url}\t탭x')
				fwrite(output2_file_path,'탭x')
				print(f'{idx} / {total_cnt} 탭 메뉴가 존재 하지 않습니다.')
				continue

			driver.get(search_url)

			driver.execute_script("window.scrollTo(0, 20000);")
			time.sleep(1)
			blogs_url_tag = '#content > section > div.api_subject_bx > div > div.keyword_challenge_wrap > ul > li > div > div.user_box > a'
			blog_list = driver.find_elements(By.CSS_SELECTOR,blogs_url_tag)
			main_blog_url = re.sub('(?<=/)[0-9.]+','', blog_url)
			if debug : print(f'Input Blog URL : {blog_url} 가져온 블로그 갯수 : {len(blog_list)}')
			for rank, blog_info in enumerate(blog_list, start=1) :
				blog_link = blog_info.get_attribute('href')
				if debug : print(f'{rank}\t{blog_link}')
				if main_blog_url in blog_link  :
					exist_flag = True
					break

				if rank > 20 :

					break

			if not exist_flag :
				rank = '0,0'

			fwrite(output1_file_path,f'{keyword}\t{tab_keyword}\t{blog_url}\t{rank}')
			fwrite(output2_file_path,rank)

			print(f'{idx} / {total_cnt} 키워드 : {keyword} - {tab_keyword} // 순위 : {rank}')

		except TimeoutError as e :
			timeour_err = f'{idx} / {total_cnt} 키워드 : {keyword} - {tab_keyword} - Timeout'
			err_string = f'error : {e}'
			print(f'{idx}번째 데이터에서 시간초과 오류 발생')
			input_data = {'reason' : err_string, 'data' : timeour_err }
			err_logging(input_data)
			fwrite(error_log_file_path,f'{keyword}\t{tab_keyword}\t{blog_url}')
			continue

		except Exception as e :
				err_string = f'error : {e}'
				print(err_string)
				input_data = {'reason' : err_string}
				err_logging(input_data)
		
	driver.quit()




# ===============================================================================
#                            Program infomation
# ===============================================================================

__author__ = '김홍연'
__requester__ = '방석호'
__registration_date__ = '230104'
__latest_update_date__ = '230104'
__version__ = 'v1.00'
__title__ = '220902 스마트블록 순위체크 프로그램'
__desc__ = '220902 스마트블록 순위체크 프로그램'
__changeLog__ = {
	'v1.00': ['Initial Release.'],
}
version_lst = list(__changeLog__.keys())

full_version_log = '\n'
short_version_log = '\n'

for ver in __changeLog__:
	full_version_log += f'{ver}\n' + '\n'.join(['    - ' + x for x in __changeLog__[ver]]) + '\n'

if len(version_lst) > 5:
	short_version_log += '.\n.\n.\n'
	short_version_log += f'{version_lst[-2]}\n' + '\n'.join(['    - ' + x for x in __changeLog__[version_lst[-2]]]) + '\n'
	short_version_log += f'{version_lst[-1]}\n' + '\n'.join(['    - ' + x for x in __changeLog__[version_lst[-1]]]) + '\n'

# ===============================================================================
#                                 Main Code
# ===============================================================================

if __name__ == '__main__':

	ctypes.windll.kernel32.SetConsoleTitleW(f'{__title__} {__version__} ({__latest_update_date__})')

	sys.stdout.write(f'{__title__} {__version__} ({__latest_update_date__})\n')

	sys.stdout.write(f'{short_version_log if short_version_log.strip() else full_version_log}\n')

	run()