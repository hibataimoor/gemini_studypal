# Gemini StudyPal

## Project Overview

Gemini StudyPal is a powerful, multimodal study assistant built using Streamlit and the Google Gemini API. It allows users to upload images of their handwritten notes or textbook pages and instantly transforms them into various structured study materials.

The application leverages Gemini's multimodal capabilities to analyze complex visual data and generate tools like flashcards, quizzes, explanations, summaries, and vocabulary lists.

## Features

Gemini StudyPal provides a few core study tools, accessible via tabs after uploading your notes:

1.  **Flashcards:** Generates a set of key terms and concepts with associated questions and answers.
2.  **Quiz:** Creates a multiple-choice quiz (10 questions) based on the content of the notes, complete with correct answers and explanations.
3.  **Explainer/Solver:** Provides a clear, step-by-step solution for complex problems or a simple explanation for the most difficult concept found in the notes.
4.  **Video Tutor:** Analyzes the notes to determine the most beneficial topic and suggests a relevant educational YouTube video for deeper understanding.

### 1. Prerequisites

* Python (3.9+)
* A Gemini API Key (Obtain one from [Google AI Studio])

### 2. Clone the Repository & Install Prerequisites
```bash
git clone https://github.com/hibataimoor/gemini_studypal
cd gemini_studypal
pip install -r requirements.txt
