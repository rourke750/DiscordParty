import requests
import asyncio
import random

from ..views import views

QUIZ_URL = 'https://the-trivia-api.com/api/questions'

def get_question():
    response = requests.get(QUIZ_URL)
    if response.status_code == 200:
        return response.json()
        
async def start_quiz(message, view):
    response = get_question()
        
    spot = random.randrange(0, 6, 1)
    selection = response[spot]
    correct_answer = selection['correctAnswer']
    incorrect_answers = selection['incorrectAnswers']
    
    # merge answers together
    all_answers = [correct_answer]
    all_answers.extend(incorrect_answers)
    all_answers.sort()
    
    category = selection['category']
    question = selection['question']
    
    correct_answer_position = 0
    for q in all_answers:
        if q == correct_answer:
            break
        correct_answer_position = correct_answer_position + 1
    
    new_response = f'Category: {category}\n{question}\na: {all_answers[0]}\nb: {all_answers[1]}\nc: {all_answers[2]}\nd: {all_answers[3]}'
    
    view.correct_answer_letter = ['a','b','c','d'][correct_answer_position]

    await message.edit(content=new_response, view=view)
    
    # now lets wait for quiz to end
    await view.quiz_ended(view.DELAYED_TIME)
    
    # now check if we should end the quiz
    if view.is_quiz_ended():
        # it ended send the results and return
        await view.send_results()
        return
    # clear the labels and any other stale data for next question
    view.clear(True)
    # now lets get our next question
    asyncio.create_task(start_quiz(message, view))
    
async def track_quiz(message):
    view = views.QuizView(message)
    id = message.id
    # start the quiz in a new task
    asyncio.create_task(start_quiz(message, view))
    