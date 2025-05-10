import traceback
import os

from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from django.shortcuts import render
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from webdriver_manager.chrome import ChromeDriverManager

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

import undetected_chromedriver as uc

import time
from typing import List
from selenium.webdriver.remote.webelement import WebElement


@api_view(['GET'])
def getReviewsOld(request):
    query: str = request.GET.get('q')
    if not query:
        return Response({"Error": "Missing 'q' parameter"}, status=status.HTTP_400_BAD_REQUEST)

    options = Options()
    # options.add_argument(
    #     "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    # )
    # options.headless = True
    # options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--enable-unsafe-webgpu")
    options.add_argument("--enable-unsafe-swiftshader")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--window-size=1920,1080")
    options.binary_location = "/usr/bin/google-chrome"

    service = ChromeService(ChromeDriverManager().install())
    driver = uc.Chrome(options=options, service=service, use_subprocess=True)

    driver.set_window_position(-2000, -2000)

    def handleLink(request, query_url, driver: uc.Chrome):
        print("Handling link:", query_url)
        time.sleep(2)
        driver.get(query_url)
        time.sleep(2)

        try:
            maps_element_xpath = "//div[contains(@class,'YmvwI') and contains(@jsname,'bVqjv') and normalize-space(text())='Maps']"
            print("Trying to find maps element...")
            # driver.save_screenshot("headless_debug.png")
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, maps_element_xpath))
            )

            print("Found maps element, trying to click...")
            maps_element = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, maps_element_xpath))
            )

            print("Found maps element")
            # driver.save_screenshot("debug_before_maps_click_attempt.png")

            clicked_successfully = False

            try:
                print("Trying to click maps element...")
                driver.execute_script(
                    "arguments[0].scrollIntoView(true);", maps_element)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", maps_element)
                WebDriverWait(driver, 10).until(
                    EC.url_contains("maps.google.com") or EC.url_contains(
                        "google.com/maps")
                )
                # driver.save_screenshot(
                #     "debug_after_maps_click.png")
                clicked_successfully = True
            except Exception as e:
                print("Error clicking maps element:", e)

        except Exception as e:
            print("Error handling link:", e)

    fetch_query = True
    if query.startswith("http") or query.startswith("https"):
        handleLink(request, query, driver)
        fetch_query = False
    search_url = f"https://www.google.com/maps/search/{query.replace(' ','+')}"

    def handleMultipleSearchResults(driver: uc.Chrome, Response: Response, By: By, WebDriverWait: WebDriverWait, EC: EC, status: status):
        titles = []
        title_checker = set()
        try:
            multiple_search_sections_relative_xpath = "//div[contains(@class, 'Nv2PK')]/a[@aria-label]"
            multiple_search_sections: List[WebElement] = WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.XPATH, multiple_search_sections_relative_xpath)))

            for section_anchor_tag in multiple_search_sections:
                title: str = section_anchor_tag.get_attribute("aria-label")
                if title.lower() in titles:
                    return None
                if title:
                    title_checker.add(title.strip().lower())
                    titles.append(title.strip())

            return Response({'titles': titles}, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'error': str(e), 'message': 'Major failure in processing multiple search results.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        if fetch_query:
            driver.get(search_url)

        REVIEWS_FOUND = False
        try:
            review_button_relative_xpath = "//button[role='tab' and contains(@aria-label, 'Reviews') or contains(@aria-label, 'Reviews ') or contains(., 'Reviews ')]"
            review_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, review_button_relative_xpath)))
            time.sleep(0.5)
            review_button.click()
            REVIEWS_FOUND = True

            time.sleep(2)
        except:
            titles_of_multiple_search_results = handleMultipleSearchResults(
                driver, Response, By, WebDriverWait, EC, status)
            return titles_of_multiple_search_results if titles_of_multiple_search_results else Response({'error': 'Found Multiple Buisnesses with same name'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        reviews = []
        try:
            review_section_relative_xpath = "//div[contains(@class,'kA9KIf') and contains(@class,'XiKgde')]"
            reviews_section = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, review_section_relative_xpath)))

            def extract_reviews(reviews_section: uc.Chrome, reviews_list: list):
                single_review_section_relative_xpath = "//div[contains(@class,'jftiEf') and contains(@class,'fontBodyMedium')]"
                try:
                    single_review_sections = reviews_section.find_elements(
                        By.XPATH, single_review_section_relative_xpath)

                    if not single_review_sections:
                        driver.execute_script(
                            "const reviews_div=document.getElementsByClassName('m6QErb DxyBCb kA9KIf dS8AEf XiKgde'); reviews_div[0].scrollTop=reviews_div[0].scrollHeight;")
                        time.sleep(5)
                        single_review_sections = reviews_section.find_elements(
                            By.XPATH, single_review_section_relative_xpath)

                    for review in single_review_sections:
                        try:
                            reviewer_name = review.find_element(
                                By.CLASS_NAME, "d4r55").text

                            review_content = review.find_element(
                                By.CLASS_NAME, "wiI7pd").text
                            review_stars_section = None
                            try:
                                review_stars_section = review.find_element(
                                    By.CLASS_NAME, "kvMYJc")
                            except:
                                pass
                            review_stars = review_stars_section.get_attribute(
                                "aria-label") if review_stars_section else None

                            review_date = None
                            try:
                                review_date = review.find_element(
                                    By.CLASS_NAME, "rsqaWe").text
                                if not review_date:
                                    review_date = review.find_element(
                                        By.CLASS_NAME, "xRkPPb").text
                            except:
                                pass

                            reviewer_image = review.find_element(
                                By.CLASS_NAME, "NBa7we").get_attribute("src")
                            reviews_list.append(
                                {
                                    "Name": reviewer_name if reviewer_name else "Anonymous",
                                    "Stars": review_stars if review_stars else "NA",
                                    "Date": review_date if review_date else "NA",
                                    "Review": review_content if review_content else "NA",
                                    "Image": reviewer_image if reviewer_image else "",
                                }
                            )
                        except Exception as e:
                            print("Error finding Reviews", e)

                except:
                    pass

            if REVIEWS_FOUND:
                extract_reviews(reviews_section, reviews)
        except:
            pass
        return Response({"reviews": reviews}, status=status.HTTP_200_OK)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            "query": query,
            "status": "Scraping simulation failed",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    finally:
        if driver:
            driver.quit()


DEBUG_DIR = "selenium_debug"
os.makedirs(DEBUG_DIR, exist_ok=True)
