# Machine Learning Project: predicting apartment rents in Turkey using real estate data from emlakjet.com

## Description

This project is designed to apply my data science skills to a real world, business-oriented environment. Specifically, the goal of this project is to provide insights into the real estate market in Turkey, and develop a ML model capable of accurately predicting apartment rents. 

## Features

- **Web scraping**: Collects apartment data from Turkish leading real estate portal emlakjet.com and saves it as an Excel file
- **Data import, validation, cleaning and preprocessing**: Imports the data, transforms and cleans the variables, and handles missing values
- **Exploratory Data Analysis and Data Visualization**: Analyzes which provinces and districts have the highest average rent, average apartment size, average number of rooms and average building age, and represent this information in graphs and maps, as well as exploring and plotting correlations between features.
- **Feature engineering**: Target and One Hot Encoding of features to make the data suitable for ML models
- **Machine Learning**: Uses 12 ML models (Linear Regression, Ridge, Lasso, SVR, SGD, KNeighbors, Decision Trees, Gradient Boosting, Random Forest, AdaBoost with decision trees, Light GBM, and CatBoost) to fit the data with cross-validation, and selects the one with lowest RMSE.
- **Hyperparameter tuning and features importance**: Uses optuna to automate hyperparameter tuning and get the best model, and represents graphically features importance.

## Data Sources

- Apartments data: https://www.emlakjet.com/kiralik-konut/istanbul/emlakcidan/
- GeoJSON files for creating province and district-level maps visualizing data: https://data.humdata.org/dataset/geoboundaries-admin-boundaries-for-turkey

## Technologies used

- **Python**: Core programming language
- **Jupyter Notebook**: For development and interactive analysis
- **BeautifulSoup, html, requests and urllib3**: For web scraping
- **Pandas, NumPy and unidecode**: For data import, cleaning and preprocessing
- **Matplotlib, Seaborn and Geopandas**: For data visualization
- **sklearn, lightgbm and CatBoost**: For feature engineering, ML modeling and cross-validation
- **optuna**: For hyperparameter tuning

## Project structure

- **Step 1**: Web scraping apartment data from emlakjet.com
- **Step 2**: Data preprocessing
- **Step 3**: Exploratory Data Analysis and Data Visualization
- **Step 4**: Feature engineering
- **Step 5**: Developing ML models to predict rental prices and model selection
- **Step 6**: Hyperparameter tuning and feature importances

## How to Run the Project

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/hectormarthinez/emlakjet_project.git
   cd emlakjet_project

2. **Install Dependencies**: Ensure you have Python installed. Then, run:
   ```bash
   pip install -r requirements.txt

3. **Run the Notebook**: Launch Jupyter Notebook, open emlakjet_project.ipynb and run the cells sequentially.
   ```bash
   jupyter notebook

## Potential future improvements

- Get sociodemographic data at the district and neighborhood level, for instance, from official sources like TÜIK or specialized websites like endeksa.com
- Implement advanced deep learning models with Keras, TensorFlow or PyTorch and check whether its predictions are more accurate
- Use this model to predict the rents of apartments for sale in emlakjet.com and calculate the annual ROI of apartments.
- Deploy this model to production: automatize webscraping, data cleaning/preprocessing, and model fine-tuning with AWS and Flask

## Author
Héctor Martínez

LinkedIn: https://www.linkedin.com/in/hectormarthinez/
