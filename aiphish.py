import openai


def generate_phishing_email(profile, openapi_key: str):
    openai.api_key = openapi_key

    gpt_query = "Write an email (without subject) to this person that makes them click a link. Clearly mark the location of the link with [INSERT LINK HERE]. My name is Bob. This is their description from Linkedin:\n"
    gpt_query += "user_information" + ".\n\nThank you!"

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=gpt_query,
        temperature=0.7,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    print(response.choices[0].text)


def send_email(mail_text: str, address: str):
    pass

