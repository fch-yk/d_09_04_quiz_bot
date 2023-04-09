import os


def load_questions(folder_name):
    files_names = os.listdir(path=folder_name)
    questions = {}
    for file_name in files_names:
        file_path = os.path.join(folder_name, file_name)
        with open(file_path, mode='r', encoding='KOI8-R') as file:
            question_lines = False
            question_text = ''
            answer_lines = False
            answer_text = ''
            for line in file:
                if not line.strip():
                    if answer_lines:
                        question_text = question_text.replace(
                            '\n',
                            ' '
                        ).strip()
                        answer_text = answer_text.replace(
                            '\n',
                            ' '
                        ).strip()
                        questions[question_text] = answer_text
                        question_lines = False
                        question_text = ''
                        answer_lines = False
                        answer_text = ''
                    continue

                if line.startswith('Вопрос'):
                    question_lines = True
                    continue

                if line.startswith('Ответ:'):
                    answer_lines = True
                    question_lines = False
                    continue

                if question_lines:
                    question_text += line

                if answer_lines:
                    answer_text += line
    return questions
