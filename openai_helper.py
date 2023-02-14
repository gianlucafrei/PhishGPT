import openai


def generate_phishing_email(profile: dict, openapi_key: str) -> str:
    openai.api_key = openapi_key

    user_information = profile["full_name"] + "\n" + profile["summary"] + "\n\n"

    experiences = profile["experiences"]
    user_information += "Work experiences:\n"
    for experience in experiences:
        user_information += experience["title"] + " at " + experience["company"] + "\n"

    user_information += "\n"

    educations = profile["education"]
    user_information += "Attended schools:\n"
    for education in educations:
        user_information += education["school"] + "\n"

    gpt_query = "Write an email (signed as Bob and without the subject) to the following person that makes them click a link. Mark the location of the link with [INSERT LINK HERE]. In the mail, take in consideration his Linkedin description:\n"
    gpt_query += user_information + ".\n\nThank you!"

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=gpt_query,
        temperature=0.7,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    return response.choices[0].text
