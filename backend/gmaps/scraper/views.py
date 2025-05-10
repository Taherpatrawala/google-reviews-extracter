import traceback  # Import traceback for better error logging if not already there
import os
# For ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
# Keep this for options configuration
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
    options.headless = True
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--enable-unsafe-webgpu")
    options.add_argument("--enable-unsafe-swiftshader")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--window-size=1920,1080")

    # options.add_argument("--disable-blink-features=AutomationControlled")
    # options.add_experimental_option("excludeSwitches", ["enable-automation"])
    # options.add_experimental_option('useAutomationExtension', False)

    service = ChromeService(ChromeDriverManager().install())
    driver = uc.Chrome(options=options, service=service, use_subprocess=True)

    def handleLink(request, query_url, driver: uc.Chrome):
        print("Handling link:", query_url)
        time.sleep(2)
        driver.get(query_url)
        time.sleep(2)

        try:
            maps_element_xpath = "//div[contains(@class,'YmvwI') and contains(@jsname,'bVqjv') and normalize-space(text())='Maps']"
            print("Trying to find maps element...")
            driver.save_screenshot("headless_debug.png")
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, maps_element_xpath))
            )

            print("Found maps element, trying to click...")
            maps_element = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, maps_element_xpath))
            )

            print("Found maps element, saving screenshot...")
            driver.save_screenshot("debug_before_maps_click_attempt.png")

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
                driver.save_screenshot(
                    "debug_after_maps_click.png")
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


# Selenium and related imports (some might be used by uc indirectly or by your existing logic)

# Webdriver Manager

# Undetected Chromedriver

# Create a directory for debug files if it doesn't exist (optional, but good practice from previous versions)
DEBUG_DIR = "selenium_debug"
os.makedirs(DEBUG_DIR, exist_ok=True)


# @api_view(['GET'])
# def getReviewsUndetected(request):
#     query: str = request.GET.get('q')
#     if not query:
#         return Response({"Error": "Missing 'q' parameter"}, status=status.HTTP_400_BAD_REQUEST)

#     options = Options()
#     # options.add_argument("--headless=new") # Headless mode might sometimes be more detectable by anti-bot systems. Test with and without.
#     options.add_argument("--disable-gpu")
#     options.add_argument("--no-sandbox")
#     # The following unsafe flags might not be necessary with undetected-chromedriver and could potentially cause issues.
#     # Consider removing them if you encounter problems, or if uc handles these aspects.
#     # options.add_argument("--enable-unsafe-webgpu")
#     # options.add_argument("--enable-unsafe-swiftshader")
#     # options.add_argument("--disable-software-rasterizer")
#     options.add_argument("--window-size=1920,1080")
#     # Add a common user-agent; uc might also handle this, but it doesn't hurt.
#     options.add_argument(
#         "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36")
#     options.add_argument("--lang=en-US")

#     # --- Integration of undetected-chromedriver ---
#     driver = None  # Initialize driver to None
#     try:
#         print("DEBUG: Setting up ChromeService with ChromeDriverManager...")
#         service = ChromeService(ChromeDriverManager().install())
#         print("DEBUG: Initializing undetected_chromedriver...")
#         # Use uc.Chrome instead of webdriver.Chrome
#         # Pass the existing 'options' object.
#         # 'use_subprocess=True' is often recommended for uc for better isolation.
#         driver = uc.Chrome(options=options, service=service,
#                            use_subprocess=True)
#         print("DEBUG: undetected_chromedriver initialized.")

#         # It's a good practice to ensure the driver object was created
#         if driver is None:
#             print("CRITICAL ERROR: undetected_chromedriver failed to initialize.")
#             return Response({
#                 "query": query,
#                 "status": "Scraping simulation failed",
#                 "error": "Failed to initialize Chrome driver (uc.Chrome)."
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#         # Your existing logic starts here
#         # Renamed request to request_obj to avoid conflict
#         def handleLink(request, query_url, driver: uc.Chrome):  # Explicitly type hint driver
#     print(f"Attempting to navigate to URL: {query_url}")
#     driver.get(query_url)
#     current_url_after_get = driver.current_url
#     print(f"Successfully navigated. Current URL is: {current_url_after_get}")
#     driver.save_screenshot("debug_after_initial_get.png")
#     print("Screenshot taken: debug_after_initial_get.png (after initial driver.get)")

#     # It's possible the "Maps" tab is on a Google Search results page, not directly a Maps URL
#     # The goal is to click this "Maps" tab to transition to the Maps view.

#     try:
#         # More specific XPath: ensuring it's the div with the exact text "Maps"
#         maps_element_xpath = "//div[contains(@class,'YmvwI') and contains(@jsname,'bVqjv') and normalize-space(text())='Maps']"
#         print(f"Waiting for 'Maps' element with XPath: {maps_element_xpath}")

#         # Wait for the element to be present first, then check if clickable
#         WebDriverWait(driver, 15).until(
#             EC.presence_of_element_located((By.XPATH, maps_element_xpath))
#         )
#         print("'Maps' element is present in the DOM.")

#         # Now get the element and wait for it to be clickable
#         maps_element = WebDriverWait(driver, 15).until(
#             EC.element_to_be_clickable((By.XPATH, maps_element_xpath))
#         )
#         print("'Maps' element is deemed clickable by WebDriverWait.")

#         # --- Extended Debugging for the element ---
#         print(
#             f"Element Details: Tag='{maps_element.tag_name}', Text='{maps_element.text}'")
#         print(
#             f"Is Displayed: {maps_element.is_displayed()}, Is Enabled: {maps_element.is_enabled()}")
#         print(f"Location: {maps_element.location}, Size: {maps_element.size}")
#         driver.save_screenshot("debug_before_maps_click_attempt.png")
#         print("Screenshot taken: debug_before_maps_click_attempt.png")
#         # --- End Extended Debugging ---

#         clicked_successfully = False
#         # Attempt 1: JavaScript Click (Often most reliable for non-button elements)
#         try:
#             print("Attempting JavaScript click on 'Maps' element...")
#             # Scroll into view first
#             driver.execute_script(
#                 "arguments[0].scrollIntoView(true);", maps_element)
#             time.sleep(0.5)  # Brief pause for scroll to settle
#             driver.execute_script("arguments[0].click();", maps_element)
#             print("JavaScript click executed.")
#             # Wait for a URL change or a specific element on the new page to confirm the click worked
#             WebDriverWait(driver, 10).until(
#                 # More likely URL after clicking "Maps" tab on search
#                 EC.url_contains("maps.google.com/search")
#                 # Or EC.url_contains("tbm=lcl") for local results / maps tab
#                 # Or wait for a specific element unique to the maps view:
#                 # EC.presence_of_element_located((By.ID, "map-canvas")) # Example ID
#             )
#             print("Page transition confirmed after JavaScript click.")
#             clicked_successfully = True
#         except Exception as e_js_click:
#             print(
#                 f"JavaScript click failed or timed out waiting for URL change: {e_js_click}")
#             driver.save_screenshot("debug_js_click_failed.png")
#             print("Screenshot taken: debug_js_click_failed.png")

#         # Attempt 2: ActionChains Click (If JS click failed)
#         if not clicked_successfully:
#             try:
#                 print("Attempting ActionChains click on 'Maps' element...")
#                 ActionChains(driver).move_to_element(
#                     maps_element).click().perform()
#                 print("ActionChains click performed.")
#                 WebDriverWait(driver, 10).until(
#                     # Or other relevant condition
#                     EC.url_contains("maps.google.com/search")
#                 )
#                 print("Page transition confirmed after ActionChains click.")
#                 clicked_successfully = True
#             except Exception as e_action_click:
#                 print(
#                     f"ActionChains click failed or timed out waiting for URL change: {e_action_click}")
#                 driver.save_screenshot("debug_actionchains_click_failed.png")
#                 print("Screenshot taken: debug_actionchains_click_failed.png")

#         # Attempt 3: Standard Selenium Click (As a last resort)
#         if not clicked_successfully:
#             try:
#                 print("Attempting standard .click() on 'Maps' element...")
#                 maps_element.click()
#                 print("Standard .click() performed.")
#                 WebDriverWait(driver, 10).until(
#                     # Or other relevant condition
#                     EC.url_contains("maps.google.com/search")
#                 )
#                 print("Page transition confirmed after standard click.")
#                 clicked_successfully = True
#             except Exception as e_standard_click:
#                 print(
#                     f"Standard .click() failed or timed out waiting for URL change: {e_standard_click}")
#                 driver.save_screenshot("debug_standard_click_failed.png")
#                 print("Screenshot taken: debug_standard_click_failed.png")

#         if clicked_successfully:
#             print("Successfully clicked the 'Maps' element and page transitioned.")
#             final_url = driver.current_url
#             print(f"Final URL after click: {final_url}")
#         else:
#             print(
#                 "All click attempts for 'Maps' element failed to produce the expected page transition.")
#             # This 'raise' will be caught by the outer except block
#             raise Exception("All click attempts failed for the Maps element.")

#     except Exception as e:
#         print(
#             f"An error occurred in handleLink while trying to click 'Maps' element: {e}")
#         driver.save_screenshot("debug_handlelink_error.png")
#         print("Screenshot taken: debug_handlelink_error.png")
#         print(traceback.format_exc())  # Print full traceback
#         # Re-raise the exception so the main try-except in getReviewsOld can handle it
#         # or return an appropriate error Response from here if preferred.
#         raise  # This will be caught by the outer try-except in getReviewsOld
#         fetch_query = True
#         if query.startswith("http://") or query.startswith("https://"):
#             # Check if it's a Google search link that needs to be converted to maps
#             if "google.com/search" in query:
#                 print(f"DEBUG: Query is a Google search link: {query}")
#                 # Pass the original request object
#                 handleLink(request, query, driver)
#                 # After clicking maps, the current page should be a maps page.
#                 # We might not need to set fetch_query to False if we want to re-search on maps.
#                 # However, if handleLink successfully navigates to a specific map,
#                 # then the subsequent search_url might be redundant or wrong.
#                 # This logic might need refinement based on expected behavior.
#                 # For now, assuming handleLink gets us to the right map page.
#                 # To prevent navigating to search_url if link handling is supposed to be final
#                 fetch_query = False
#             else:
#                 # If it's a direct link not to a google search page, just navigate to it.
#                 print(
#                     f"DEBUG: Query is a direct link (not Google search): {query}")
#                 driver.get(query)
#                 time.sleep(3)  # Allow page to load
#                 fetch_query = False

#         # This search_url will be used if fetch_query is True
#         search_url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"

#         def handleMultipleSearchResults(drv: uc.Chrome, resp_class: type, by_class: type, wait_class: type, ec_class: type, stat_class: type):
#             titles = []
#             print("DEBUG: Inside handleMultipleSearchResults")
#             # drv.save_screenshot(os.path.join(DEBUG_DIR, f"{query}_before_multiple_search.png"))
#             try:
#                 # This XPath looks for anchor tags within a specific div structure, common for search results.
#                 multiple_search_sections_relative_xpath = "//div[contains(@class, 'Nv2PK')]/a[@aria-label and @href]"
#                 print(
#                     f"DEBUG: Waiting for multiple search sections with XPath: {multiple_search_sections_relative_xpath}")

#                 multiple_search_sections = wait_class(drv, 10).until(  # Increased wait slightly
#                     ec_class.presence_of_all_elements_located(
#                         (by_class.XPATH, multiple_search_sections_relative_xpath))
#                 )

#                 print(
#                     f"DEBUG: Found {len(multiple_search_sections)} potential multiple search result sections (these are <a> tags).")
#                 # drv.save_screenshot(os.path.join(DEBUG_DIR, f"{query}_found_multiple_search.png"))

#                 for i, section_anchor_tag in enumerate(multiple_search_sections):
#                     print(
#                         f"\n--- Processing Multiple Search Result (Anchor Tag) {i+1} ---")
#                     title = section_anchor_tag.get_attribute("aria-label")
#                     href = section_anchor_tag.get_attribute("href")

#                     if title and href:  # Ensure both title and href exist
#                         title = title.strip()
#                         print(
#                             f"DEBUG: Extracted title: '{title}', Href: '{href}'")
#                         if "google.com/maps" in href:  # Check if it's a valid maps link
#                             # Store as dict
#                             titles.append({"title": title, "url": href})
#                         else:
#                             print(
#                                 f"DEBUG: Skipping result, href not a maps link: {href}")
#                     else:
#                         print(
#                             f"DEBUG: Skipping section {i+1}, missing title or href. Title: '{title}', Href: '{href}'")

#                 if not titles:
#                     print(
#                         "DEBUG: No valid titles extracted from multiple search results.")
#                     # drv.save_screenshot(os.path.join(DEBUG_DIR, f"{query}_no_valid_titles_multiple.png"))
#                     # Fallback: if no titles with valid hrefs, maybe the page structure is different
#                     # Try a broader approach to see if any results are listed
#                     broader_results_xpath = "//div[@role='article']//div[@role='heading'] | //div[contains(@aria-label, 'Results for')]//a[@aria-label]"
#                     try:
#                         broader_elements = wait_class(drv, 5).until(
#                             ec_class.presence_of_all_elements_located((by_class.XPATH, broader_results_xpath)))
#                         if broader_elements:
#                             print(
#                                 f"DEBUG: Fallback found {len(broader_elements)} broader result elements.")
#                             for el in broader_elements:
#                                 el_title = el.get_attribute(
#                                     'aria-label') or el.text
#                                 el_href = el.get_attribute(
#                                     'href') if el.tag_name == 'a' else None
#                                 if el_title and el_title.strip():
#                                     titles.append(
#                                         {"title": el_title.strip(), "url": el_href})
#                     except:
#                         print("DEBUG: Fallback for broader results also failed.")

#                 return resp_class({'titles': titles}, status=stat_class.HTTP_200_OK if titles else stat_class.HTTP_404_NOT_FOUND)

#             except Exception as e_multi:
#                 print(
#                     f"CRITICAL ERROR in handleMultipleSearchResults: {e_multi}")
#                 traceback.print_exc()
#                 # drv.save_screenshot(os.path.join(DEBUG_DIR, f"{query}_ERROR_multiple_search.png"))
#                 # with open(os.path.join(DEBUG_DIR, f"{query}_ERROR_multiple_search.html"), "w", encoding="utf-8") as f_err:
#                 #    f_err.write(drv.page_source)
#                 return resp_class({'error': str(e_multi), 'message': 'Failure in processing multiple search results.'}, status=stat_class.HTTP_500_INTERNAL_SERVER_ERROR)

#         # Main try block for scraping logic
#         print(
#             f"DEBUG: fetch_query is {fetch_query}. If true, will navigate to: {search_url if fetch_query else 'N/A'}")
#         if fetch_query:
#             driver.get(search_url)
#             time.sleep(3)  # Allow search results to load
#             # driver.save_screenshot(os.path.join(DEBUG_DIR, f"{query}_after_search_url_load.png"))

#         REVIEWS_FOUND_AND_CLICKED = False  # Renamed for clarity
#         try:
#             print("DEBUG: Looking for 'Reviews' button/tab...")
#             # Using a more robust relative XPath for the reviews button
#             # It looks for a button, that is a tab, and has 'Reviews' in its aria-label or text content.
#             review_button_relative_xpath = "//button[@role='tab' and (contains(@aria-label, 'Reviews') or contains(., 'Reviews')) and not(ancestor::div[contains(@style,'display: none')])]"
#             # Alternative XPaths if the above fails:
#             # review_button_relative_xpath = "//button[contains(@data-value, 'Reviews') and not(ancestor::div[contains(@style,'display: none')])]"
#             # review_button_relative_xpath = "//div[@role='tablist']//button[contains(.,'Reviews') or contains(@aria-label,'Reviews')][position()=2 or position()=1]" # Second or first button in a tablist

#             review_button = WebDriverWait(driver, 10).until(
#                 EC.element_to_be_clickable(
#                     (By.XPATH, review_button_relative_xpath))
#             )
#             print("DEBUG: 'Reviews' button found. Clicking...")
#             review_button.click()
#             REVIEWS_FOUND_AND_CLICKED = True
#             time.sleep(3)  # Wait for reviews section to load
#             print("DEBUG: 'Reviews' button clicked successfully.")
#             # driver.save_screenshot(os.path.join(DEBUG_DIR, f"{query}_reviews_button_clicked.png"))

#         except Exception as e_review_button:
#             print(
#                 f"DEBUG: 'Reviews' button not found or not clickable. Error: {e_review_button}")
#             print(
#                 "DEBUG: Assuming this might be a search results page, looking for multiple search results...")
#             # driver.save_screenshot(os.path.join(DEBUG_DIR, f"{query}_FAIL_reviews_button.png"))
#             # with open(os.path.join(DEBUG_DIR, f"{query}_FAIL_reviews_button.html"), "w", encoding="utf-8") as f_html:
#             #    f_html.write(driver.page_source)
#             return handleMultipleSearchResults(driver, Response, By, WebDriverWait, EC, status)

#         reviews_data_list = []  # Renamed for clarity
#         if REVIEWS_FOUND_AND_CLICKED:  # Only try to extract if button was clicked
#             print("DEBUG: Attempting to extract reviews data...")
#             try:
#                 # XPath for the container of all reviews. This might need adjustment.
#                 # Look for a scrollable area or a list that contains individual review items.
#                 review_section_container_xpath = "//div[starts-with(@aria-label,'Scrollable') and contains(@aria-label, 'reviews')] | //div[contains(@class,'review-dialog-list')]"

#                 # Wait for the main reviews container to be present
#                 reviews_section_element = WebDriverWait(driver, 10).until(
#                     EC.presence_of_element_located(
#                         (By.XPATH, review_section_container_xpath))
#                 )
#                 print("DEBUG: Main reviews section container found.")

#                 # Function to extract individual review details
#                 def extract_reviews_from_section(section_element, extracted_list):
#                     # XPath for individual review blocks within the container.
#                     # These usually have a common class or data attribute.
#                     # More specific: a div with data-review-id and an aria-label
#                     single_review_block_xpath = ".//div[@data-review-id and @aria-label]"
#                     # Alternative: "//div[contains(@class,'jftiEf') and contains(@class,'fontBodyMedium')]" (your old one)
#                     # Alternative: ".//div[contains(@class, ' отзыв ')]" # For other languages if class names change

#                     try:
#                         print(
#                             f"DEBUG: Looking for individual review blocks with XPath: {single_review_block_xpath} within the section.")
#                         # driver.save_screenshot(os.path.join(DEBUG_DIR, f"{query}_before_find_review_blocks.png"))
#                         # It's crucial to wait for these elements to be present too
#                         WebDriverWait(section_element, 10).until(
#                             EC.presence_of_all_elements_located(
#                                 (By.XPATH, single_review_block_xpath))
#                         )
#                         single_review_elements = section_element.find_elements(
#                             By.XPATH, single_review_block_xpath)
#                         print(
#                             f"DEBUG: Found {len(single_review_elements)} individual review blocks.")

#                         if not single_review_elements:
#                             print(
#                                 "DEBUG: No individual review blocks found with the primary XPath. Trying alternative...")
#                             # Try another common pattern if the first fails
#                             single_review_block_xpath_alt = ".//div[contains(@class,'jftiEf') and .//span[contains(@class,'wiI7pd')]]"
#                             single_review_elements = section_element.find_elements(
#                                 By.XPATH, single_review_block_xpath_alt)
#                             print(
#                                 f"DEBUG: Found {len(single_review_elements)} individual review blocks with alternative XPath.")

#                         for i, review_element in enumerate(single_review_elements):
#                             print(f"--- Extracting review {i+1} ---")
#                             try:
#                                 # Extracting details. Class names are highly volatile. Prefer aria-labels or more stable attributes.
#                                 reviewer_name = review_element.find_element(
#                                     By.XPATH, ".//div[contains(@class, 'd4r55') or contains(@class,'fontBodyMedium') and not(contains(@class,'PuaHbe'))]").text

#                                 review_content_element = review_element.find_element(
#                                     By.XPATH, ".//span[@jscontroller='MZnM8e' and @class='wiI7pd']")  # Common for review text
#                                 review_content = review_content_element.text

#                                 # Check for "See more" button and click if present
#                                 try:
#                                     see_more_button = review_content_element.find_element(
#                                         By.XPATH, "./button[contains(@aria-label, 'See more')]")
#                                     print(
#                                         f"DEBUG: Clicking 'See more' for review {i+1}")
#                                     see_more_button.click()
#                                     # Brief pause for content to expand
#                                     time.sleep(0.5)
#                                     review_content = review_content_element.text  # Re-fetch expanded text
#                                 except:
#                                     pass  # No "See more" button or failed to click

#                                 review_stars_section = review_element.find_element(
#                                     By.XPATH, ".//span[contains(@aria-label, 'star')]")
#                                 review_stars = review_stars_section.get_attribute(
#                                     "aria-label")

#                                 review_date = review_element.find_element(
#                                     By.XPATH, ".//span[contains(@class, 'rsqaWe') or contains(@class,'NBa7we')]").text  # rsqaWe is common for date

#                                 reviewer_image_element = review_element.find_element(
#                                     By.XPATH, ".//img[contains(@class, 'NBa7we') or contains(@class,'gm2-avatar')]")
#                                 reviewer_image = reviewer_image_element.get_attribute(
#                                     "src")

#                                 extracted_list.append({
#                                     "Name": reviewer_name.strip() if reviewer_name else "N/A",
#                                     "Stars": review_stars.strip() if review_stars else "N/A",
#                                     "Date": review_date.strip() if review_date else "N/A",
#                                     "Review": review_content.strip() if review_content else "N/A",
#                                     "Image": reviewer_image if reviewer_image else "N/A",
#                                 })
#                                 print(
#                                     f"DEBUG: Successfully extracted review {i+1}: {reviewer_name.strip()[:30]}...")
#                             except Exception as e_extract_detail:
#                                 print(
#                                     f"DEBUG: Error extracting some details for review {i+1}. Error: {e_extract_detail}")
#                                 # Add a placeholder if a review block was found but details failed
#                                 extracted_list.append(
#                                     {"error": f"Partial data extraction failed for review {i+1}", "details": str(e_extract_detail)})
#                     except Exception as e_find_blocks:
#                         print(
#                             f"DEBUG: Error finding individual review blocks within the section. Error: {e_find_blocks}")
#                         # driver.save_screenshot(os.path.join(DEBUG_DIR, f"{query}_ERROR_find_review_blocks.png"))

#                 extract_reviews_from_section(
#                     reviews_section_element, reviews_data_list)
#                 print(
#                     f"DEBUG: Total reviews extracted: {len(reviews_data_list)}")
#                 # driver.save_screenshot(os.path.join(DEBUG_DIR, f"{query}_reviews_extracted.png"))

#             except Exception as e_reviews_section:
#                 print(
#                     f"DEBUG: Error finding or processing the main reviews section. Error: {e_reviews_section}")
#                 # driver.save_screenshot(os.path.join(DEBUG_DIR, f"{query}_ERROR_reviews_section.png"))

#         if not reviews_data_list and REVIEWS_FOUND_AND_CLICKED:
#             print("DEBUG: Reviews button was clicked, but no review data was extracted. The page structure might have changed or reviews are not available.")
#         elif not REVIEWS_FOUND_AND_CLICKED and not reviews_data_list:
#             print("DEBUG: Neither reviews button was clicked nor any reviews extracted (likely went to multiple search results).")

#         return Response({"reviews": reviews_data_list if reviews_data_list else "No reviews found or extracted."}, status=status.HTTP_200_OK)

#     except Exception as e:
#         print(f"CRITICAL ERROR during scraping for query '{query}': {e}")
#         traceback.print_exc()
#         if driver:  # Save screenshot on critical error if driver exists
#             driver.save_screenshot(os.path.join(
#                 DEBUG_DIR, f"{query}_CRITICAL_ERROR.png"))
#             with open(os.path.join(DEBUG_DIR, f"{query}_CRITICAL_ERROR.html"), "w", encoding="utf-8") as f_crit_err:
#                 try:
#                     f_crit_err.write(driver.page_source)
#                 except:
#                     pass  # driver might be in a bad state

#         return Response({
#             "query": query,
#             "status": "Scraping simulation failed",
#             "error_type": type(e).__name__,
#             "error_message": str(e)
#         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     finally:
#         if driver:
#             print("DEBUG: Closing driver...")
#             try:
#                 driver.quit()
#                 print("DEBUG: Driver closed successfully.")
#             except Exception as e_quit:
#                 print(f"DEBUG: Error during driver.quit(). Error: {e_quit}")
