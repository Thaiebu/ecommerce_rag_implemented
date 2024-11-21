import asyncio
from playwright.async_api import async_playwright
import csv

async def scrape_product_details(input_html_path):
    async with async_playwright() as p:
        # Launch the browser and create a new page
        browser = await p.chromium.launch()  # Missing 'await' fixed
        page = await browser.new_page()  # Missing 'await' fixed

        # Load the local HTML file
        with open(input_html_path, "r", encoding="utf-8") as file:
            html_content = file.read()

        await page.set_content(html_content)  # Missing 'await' fixed

        # List to store product details
        product_details = []

        # Locate all product containers
        product_elements = await page.query_selector_all(
            "div[data-component-type='s-search-result']"
        )

        for product in product_elements:
            # Extract product name
            name_element = await product.query_selector("h2 > a > span")
            product_name = await name_element.inner_text() if name_element else "N/A"
            
            # Extract price
            price_whole = await product.query_selector("span.a-price-whole")
            price_fraction = await product.query_selector("span.a-price-fraction")
            price = (
                f"{await price_whole.inner_text()}.{await price_fraction.inner_text()}"
                if price_whole and price_fraction
                else "N/A"
            )
            
            # Extract image URL
            image_element = await product.query_selector("img.s-image")
            image_url = await image_element.get_attribute("src") if image_element else "N/A"
            
            # Extract rating
            rating_element = await product.query_selector("span.a-icon-alt")
            rating = await rating_element.inner_text() if rating_element else "N/A"
            
            # Append product details to the list
            product_details.append({
                "product_name": product_name,
                "price": price,
                "image_url": image_url,
                "rating": rating
            })

        # Close the browser
        await browser.close()

        # Write to CSV
        with open("product_details.csv", "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = ["product_name", "price", "image_url", "rating"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(product_details)

        print("Scraping completed and data saved to product_details.csv")

# Run the script
input_html = "Amazon_Phones.html"
asyncio.run(scrape_product_details(input_html))
