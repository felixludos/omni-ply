
## vanilla


question, options, answer = benchmark.get_question()
prompt = benchmark.construct_prompt(question, options)
chat = [{'role': 'user', 'content': prompt}]
pred = None
while pred is None:
    response = client.get_response(chat)
    try:
        pred = judge.parse(response, options)
    except InvalidPrediction:
        pass
    except ParsingError:
        pass
    
    if pred in options:
        break
    else:
        chat.append({'role': 'assistant', 'content': response})
        chat.append({'role': 'user', 'content': 'Error: response not in options, please try again.'})
        pred = None







## omniply


class Prompter:
    @tool('pred')
    def predict(self, response: str, options: list[str]) -> str:
        """
        Predicts the response based on the given text and options.
        """
        if response not in options:
            raise ValueError(f"Response '{response}' not in options: {options}")
        return response

    @tool('response')
    def get_response(self, chat: list[dict[str,str]]) -> str:
        """
        Returns a response to the given text.
        """
        return f"Response to: {text}"

    @get_response.validator(max_retries=5)
    def check_response(self, response: str, options: list[str]) -> str:
        if response not in options:
            raise ValueError(f"Response '{response}' not in options: {options}")
        return response









