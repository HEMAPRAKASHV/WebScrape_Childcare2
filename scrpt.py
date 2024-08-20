import requests
from bs4 import BeautifulSoup
import csv
import time

def fetch_link_to_scrape(id_value):
    try:
        hrefs = []
        url = f"https://childcarefind.okdhs.org/providers?zip-code={id_value}"
        response = requests.get(url)
        scarpe_data = BeautifulSoup(response.text, 'html.parser')
        elements = scarpe_data.select('a[class*="_1b0crnf1 _1q4scjf6 z-[2]"]')
        print(f"Number of elements found: {len(elements)}")

        for element in elements:
            href = element.get('href', 'No href attribute')
            if href != 'No href attribute':
                hrefs.append(href)
        return hrefs

    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return []

def extract_data_from_link(urls, csv_filename):
    csv_headers = [
        'URL', 'ChildCare_Center', 'ChildCare_Name', 'Program_Level',
        'Contact_No', 'Email', 'Address', 'Subsidy_Contract_Number',
        'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday',
        'Infants_0_11_months', 'Toddlers_12_23_months_1yr',
        'Preschool_24_48_months_2_4_yrs', 'School_age_5_years_older',
        'Licensing_Specialist', 'Licensing_Specialist_contact_no', 
        'Visit_for_non_compliances_OBSERVED'
    ]
    
    headers_written = False  

    for url in urls:
        print(f"Processing URL: {url}")
        data = {header: 'N/A' for header in csv_headers}  # Initialize all data fields with 'N/A' by default
        try:
            full_url = f'https://childcarefind.okdhs.org/{url}'
            data['URL'] = full_url

            url_response = requests.get(full_url)
            url_data = BeautifulSoup(url_response.text, 'html.parser')

            # ChildCare information (Center, Name, Program Level)
            childcare_div = url_data.find('div', class_='_1q4scjf7')
            if childcare_div:
                data['ChildCare_Center'] = childcare_div.get_text(strip=True)
                data['ChildCare_Name'] = childcare_div.find_next_sibling('h1').get_text(strip=True) if childcare_div.find_next_sibling('h1') else 'N/A'
                data['Program_Level'] = childcare_div.find_next_sibling('h2').get_text(strip=True) if childcare_div.find_next_sibling('h2') else 'N/A'
            else:
                data['ChildCare_Center'] = 'N/A'
                data['ChildCare_Name'] = 'N/A'
                data['Program_Level'] = 'N/A'

            # Personal information (Contact No, Email, Address, Subsidy Contract Number)
            personal_info_div = url_data.find('div', class_='bd04r4l _1q4scjf6 _1umd8ia1')
            if personal_info_div:
                child_divs = personal_info_div.find_all('div', class_='_1umd8ia2')
                data['Contact_No'] = child_divs[0].get_text(strip=True) if len(child_divs) > 0 else 'N/A'
                data['Email'] = child_divs[1].get_text(strip=True) if len(child_divs) > 1 else 'N/A'
                data['Address'] = child_divs[2].get_text(strip=True) if len(child_divs) > 2 else 'N/A'
                data['Subsidy_Contract_Number'] = child_divs[3].get_text(strip=True) if len(child_divs) > 3 else 'N/A'
            else:
                data['Contact_No'] = 'N/A'
                data['Email'] = 'N/A'
                data['Address'] = 'N/A'
                data['Subsidy_Contract_Number'] = 'N/A'

            # Operating hours by day
            day_to_column_map = {
                'Monday': 'Monday',
                'Tuesday': 'Tuesday',
                'Wednesday': 'Wednesday',
                'Thursday': 'Thursday',
                'Friday': 'Friday',
                'Saturday': 'Saturday',
                'Sunday': 'Sunday'
            }

            days_divs = url_data.find_all('div', class_='yuxh4x0')
            for div in days_divs:
                dt = div.find('dt')
                dd = div.find('dd')
                if dt and dd:
                    day = dt.get_text(strip=True)
                    hours = dd.get_text(strip=True)
                    if day in day_to_column_map:
                        data[day_to_column_map[day]] = hours

            # Ages accepted
            age_li = url_data.find_all('li', class_='_18i9ibq1 _1q4scjf0')
            for li in age_li:
                age_text = li.get_text(strip=True)
                if 'Infants (0-11 months)' in age_text:
                    data['Infants_0_11_months'] = 'yes'
                elif 'Toddlers (12-23 months; 1yr.)' in age_text:
                    data['Toddlers_12_23_months_1yr'] = 'yes'
                elif 'Preschool (24-48 months; 2-4 yrs.)' in age_text:
                    data['Preschool_24_48_months_2_4_yrs'] = 'yes'
                elif 'School-age (5 years-older)' in age_text:
                    data['School_age_5_years_older'] = 'yes'

            # License information
            license_div = url_data.find('div', class_='_18i9ibq1 _1q4scjf0 _1ntxxnq0')
            if license_div:
                h2_element = license_div.find('h3', class_='_1q4scjf4')
                data['Licensing_Specialist'] = h2_element.text.strip() if h2_element else 'N/A'
                div_pppp = license_div.find('div', class_='_1ntxxnq1')
                data['Licensing_Specialist_contact_no'] = div_pppp.get_text(strip=True) if div_pppp else 'N/A'

            # License visits
            license_visits = url_data.find_all('article', class_='bd04r4l _1q4scjf0 _1elult33')
            data['Visit_for_non_compliances_OBSERVED'] = len(license_visits) if license_visits else 'N/A'

            # Write data to CSV in the loop
            with open(csv_filename, 'a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=csv_headers)
                if not headers_written:
                    writer.writeheader()
                    headers_written = True
                writer.writerow(data)

            print("Data written to CSV:")
            print(data)
            print("\n\n")
            print("...........Next................")
            
        except requests.RequestException as e:
            print(f"An error occurred while processing {url}: {e}")
        time.sleep(1) 

    return

# List of ZIP codes to process
zipcodes = ["73012", "73013", "73020"]

if __name__ == "__main__":
    for zipcode in zipcodes:
        hrefs = fetch_link_to_scrape(zipcode)
        if hrefs:
            extract_data_from_link(hrefs, 'output_data.csv')
        else:
            print(f"No hrefs found to process for ZIP code {zipcode}.")
