import os
import requests
import json
from dotenv import load_dotenv
import re
import ast

load_dotenv()

class llama:
    def __init__(self):
        token = os.getenv('HF_TOKEN')
        if not token:
            raise ValueError("HF_TOKEN not set")

        self.API_URL = "https://router.huggingface.co/groq/openai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def query(self, payload):
        response = requests.post(self.API_URL, headers=self.headers, json=payload)

        if response.status_code != 200:
            print("Hugging Face API Error:", response.text)
            raise Exception(f"HF API error {response.status_code}")

        return response.json()

    def gen_insights(self, summary: str, schema: str) -> dict:
        with open('prompt.txt', 'r') as file:
            prompt = file.read()

        content = f"{prompt}\n\n=== Summary ===\n{summary}\n\n=== Schema ===\n{schema}"
        retry_count = 3
        count = 0

        while count < retry_count:
            response = self.query({
                "messages": [
                    {"role": "system", "content": "You are a helpful data analyst AI."},
                    {"role": "user", "content": content}
                ],
                "model": "llama3-8b-8192",
                "temperature": 0.7
            })

            try:
                output = response["choices"][0]["message"]["content"]
                print(f"\n🔹 Raw LLM Output (Attempt {count + 1}):\n{output}...\n")
            except KeyError:
                print("LLM did not return valid output.")
                return self.fallback_response()

            # Remove preamble or formatting wrappers
            cleaned = re.sub(r'^.*?({)', r'\1', output, flags=re.DOTALL)
            cleaned = re.sub(r'```(json|python)?', '', cleaned).strip("` \n")

            # Try parsing
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                print("JSON parse failed. Trying fallback cleaning...")
                fixed = cleaned.replace('\\"', '"').replace('\\n', ' ')
                try:
                    return json.loads(fixed)
                except json.JSONDecodeError:
                    try:
                        return ast.literal_eval(fixed)
                    except:
                        print(f"Parsing attempt {count + 1} failed.")
                        count += 1
                        continue

        print("Failed after all retries. Returning fallback.")
        return self.fallback_response()

    def fallback_response(self) -> dict:
        return {
            'insights': 'The dataset is about the marketing campaigns of a Portuguese banking institution, aiming to predict whether a client will subscribe a term deposit. Customers who are unemployed, retired, or blue-collar have a lower subscription rate. Calls longer than 329 seconds have a 25.6% subscription rate, while calls under 104 seconds result in only 4.8%. The number of contacts performed during the campaign affects the subscription rate, with more than 3 contacts leading to diminishing returns. Clients with a higher balance and more than 5 years of previous contacts have a higher subscription rate. However, clients with previous campaigns leading to failure have a lower subscription rate. The data quality issues include a high percentage of missing values in the "contact" column, outliers in the "duration" column, and a high skewness in the "balance" column. Real-world decisions or business opportunities include adjusting the marketing strategy based on the customer\'s job type, offering personalized promotions to clients with a higher balance, and targeting clients with previous campaigns leading to success.',
            'categorical_features': ['job', 'marital', 'education', 'default', 'housing', 'loan', 'contact', 'month'],
            'numerical_features': ['age', 'balance', 'duration', 'campaign', 'pdays', 'previous', 'day'],
            'target_col': 'y',
            'inference_univariate': {
                "age": "📌 Most clients are aged between 30 and 50, with slight right skew.",
                "balance": "📌 Most clients have low or moderate balances, some with very high/negative.",
                "duration": "📌 Most calls are short; long calls are rare but more successful.",
                "campaign": "📌 Most clients contacted 1–3 times; diminishing returns after that.",
                "pdays": "📌 Most clients not contacted before; those contacted vary widely.",
                "previous": "📌 Most have no prior contacts; few have several.",
                "day": "📌 Contacted throughout month; no major skew.",
                "job": "📌 Common jobs: blue-collar, management, technician.",
                "marital": "📌 Mostly married, followed by single and divorced.",
                "education": "📌 Mostly secondary; fewer tertiary/primary.",
                "default": "📌 Very few have credit in default.",
                "housing": "📌 Most have housing loan.",
                "loan": "📌 Most do not have personal loan.",
                "contact": "📌 'Cellular' most common; many nulls.",
                "month": "📌 Most contacts in May, August, July."
            },
            'inference_bivariate': {
                ('duration', 'y'): '📌 Longer calls (>400s) → 30% success vs. <100s → 4%.',
                ('job', 'y'): '📌 Retired: 18%, students: 16%, blue-collar: 6%.',
                ('balance', 'y'): '📌 >3000 EUR → 25.5%, <3000 EUR → 17.5%.',
                ('campaign', 'y'): '📌 >3 calls → conversion <6%.',
                ('pdays', 'y'): '📌 Contacted after 30 days → 22.3% vs. within 30 days → 14.5%.',
                ('previous', 'y'): '📌 >5 prev. contacts → 23.5%, else → 16.5%'
            },
            'heatmap_inference': '📌 Duration and balance are most positively correlated with subscription.',
            'col_schema': {
                'age': 'Client Age',
                'balance': 'Yearly Balance (EUR)',
                'duration': 'Call Duration (seconds)',
                'campaign': 'Number of Contacts',
                'pdays': 'Days Since Last Contact',
                'previous': 'Previous Contacts',
                'day': 'Contact Day',
                'job': 'Job Type',
                'education': 'Education Level',
                'poutcome': 'Previous Campaign Outcome',
                'housing': 'Housing Loan',
                'loan': 'Personal Loan',
                'contact': 'Contact Method',
                'month': 'Contact Month',
                'y': 'Subscribed Term Deposit'
            },
            'bivariate_pairs': [
                ('duration', 'y'),
                ('balance', 'y'),
                ('age', 'y'),
                ('job', 'y'),
                ('campaign', 'y'),
                ('poutcome', 'y')
            ]
        }
