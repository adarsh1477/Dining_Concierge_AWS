# Dining Concierge AWS 🍽️

A cloud-based, end-to-end restaurant recommendation system powered by AWS and Yelp API. Users interact with a Lex chatbot to specify preferences, and receive dining suggestions via email.

## 🎥 Demo

[![Watch the demo](https://img.youtube.com/vi/06G1C8sMCUI/maxresdefault.jpg)](https://youtu.be/06G1C8sMCUI)

---

## 🚀 Architecture Overview

This project uses:

- **Amazon Lex** – Conversational interface
- **Lambda (LF0, LF1, LF2)** – Chat API, Lex hook, Queue worker
- **Amazon SQS** – Message queue for decoupling
- **DynamoDB** – Stores 5000+ Yelp restaurants
- **OpenSearch** – Index for fast cuisine-based search
- **SES (Simple Email Service)** – Sends email suggestions
- **S3** – Hosts the frontend
- **API Gateway** – Connects frontend to LF0

---

## 🧠 Features

- Chatbot with 3 intents: Greeting, Thank You, and DiningSuggestions
- Gathers: Location, Cuisine, Time, People Count, Email
- Sends collected data to SQS
- Worker Lambda fetches from SQS, queries OpenSearch + DynamoDB
- Delivers personalized suggestions over email

---

## 🗂️ Project Structure

Dining_Concierge_AWS/ ├── Frontend/ ├── lambdaFunctions/ │ ├── LF0.py │ ├── LF1.py │ └── LF2.py ├── OtherScripts/ │ ├── create_index.py │ ├── insert_to_opensearch.py │ ├── check_indices.py │ ├── check_opensearch_data.py │ └── check_dynamodb.py └── README.md


---

## 🔁 Flow Summary

1. User chats via Lex chatbot
2. Lex → LF1 → SQS
3. LF2 picks from SQS → OpenSearch → DynamoDB
4. Sends restaurant suggestions to user's email via SES

---

## 📨 Sample SQS Message

```json
{
  "Location": "New York",
  "Cuisine": "Indian",
  "DiningTime": "7:00 PM",
  "NumPeople": "2",
  "Email": "user@example.com"
} 

📬 Email Format
Subject: 🍽️ Your Dining Concierge Recommendation

Hello! Here are your top Indian restaurant suggestions in New York:

Biryani Express
📍 123 Curry St, NY
⭐ 4.5 | 📝 230 Reviews

Enjoy your meal!

👨‍💻 Author
Adarsh Rai – Graduate Student, NYU
GitHub: adarsh1477



