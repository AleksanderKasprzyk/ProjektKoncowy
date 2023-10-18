import requests
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret_key"
api_flask = 'http://api.nbp.pl/'
account_balance = float(0)
currency_list = []
operation_history = []


@app.route('/', methods=['GET', 'POST'])
def home_page():
    data, error_message = nbp_data('example_endpoint')  # Zaktualizuj endpoint

    if request.method == 'POST':
        if data is not None:
            if 'file' not in request.files:
                return redirect(request.url)

            file = request.files['file']
            if file.filename == '':
                return redirect(request.url)

            now = datetime.now()
            current_time = now.strftime("%Y-%m-%d %H:%M:%S")
            return render_template('Home_page.html', current_time=current_time)

        return render_template('Home_page.html', data=data, error_message=error_message)

    return render_template('Home_page.html', account_balance=account_balance, error_message=None)


@app.route('/nbp_data', methods=['GET', 'POST'])
def nbp_data(endpoint):
    if request.method == 'POST':
        response = requests.get(api_flask + endpoint)
        if response.status_code == 200:
            return response.json()
        else:
            error_message = "Error while downloading data."

        return render_template('nbp_data.html', response=response, error_message=error_message)

    return redirect(url_for('/'))


@app.route('/save_to_file', methods=['GET', 'POST'])
def save_to_file():
    if request.method == 'POST':
        data_save = \
            {
                "balance": account_balance,
                "operation_history": operation_history
            }

        # with open(filename, mode='w') as file:
        # json.dump(data, file, indent=4)

        with open('operation_history.json', mode='w') as file:
            json.dump(data_save, file, indent=4)

        currencies = nbp_data('exchangerates/tables/A/?format=json')
        if currencies:
            save_to_file('currencies_list.json', currencies)

        transaction_history = nbp_data('transaction_history')
        if transaction_history:
            save_to_file('transaction_history.json', transaction_history)

        return render_template('save_to_file.html', transaction_history=transaction_history,
                               currencies=currencies)

    return redirect(url_for('/'))


@app.route('/account_balance_operations.html', methods=['GET', 'POST'])
def account(amount):
    global account_balance
    if request.method == 'POST':
        operation_add = request.form.get('add')
        operation_substract = request.form.get('substract')

        if operation_add == 'add':
            amount = float(request.form['add_amount'])
            account_balance += amount
            operation_history.append(f"Added {amount}")
            account('balance_account.json', {"balance": account_balance})
            return render_template('/account_balance_operations.html', account=account, account_balance=account_balance,
                                   amount=amount)

        elif operation_substract == 'substract':
            if amount > account_balance:
                operation_history.append(f"Lack of sufficient resources to receive {amount}")
            else:
                amount = float(request.form['substract_amount'])
                account_balance -= amount
                operation_history.append(f"Substract {amount}")
                account('balance_account.json', {"balance": account_balance})
                return render_template('/account_balance_operations.html', account=account,
                                       account_balance=account_balance, amount=amount)

        return render_template('/account_balance_operations.html', operation_add=operation_add,
                               operation_substract=operation_substract)

    return redirect(url_for('/'))


@app.route('/personal_wallet', methods=['GET', 'POST'])
def bank_wallet():
    if request.method == 'GET':
        operation = request.form.get('operation')
        if operation == 'buy_currency':
            currency_code = request.form.get('currency_code')
            exchange_rate = nbp_data(f'exchangerates/rates/A/{currency_code}/?format=json')
            amount = float(request.form.get('amount'))

            if exchange_rate:
                buy_rate = exchange_rate['rates'][0]['mid']
                cost = buy_rate * amount
                if cost > account_balance:
                    answer = "Insufficient balance in the account."
                    return render_template('/personal_wallet', amount=amount, buy_rate=buy_rate, cost=cost,
                                           answer=answer, exchange_rate=exchange_rate, currency_code=currency_code)
                else:
                    account_balance -= cost
                    answer = "Bought {} {} for {:.2f} in PLN.".format(amount, currency_code, cost)
                    return render_template('/personal_wallet', answer=answer)
            else:
                answer = "The exchange rate cannot be obtained."
                return render_template('/personal_wallet', answer=answer)

        elif operation == 'sell_currency':
            currency_code = request.form.get('currency_code')
            exchange_rate = nbp_data(f'exchangerates/rates/A/{currency_code}/?format=json')
            amount = float(request.form.get('amount'))

            if exchange_rate:
                sell_rate = exchange_rate['rates'][0]['mid']
                sale_proceeds = sell_rate * amount
                account_balance += sale_proceeds
                answer = "Sold {} {} for {:.2f} in PLN.".format(amount, currency_code, sale_proceeds)
                return render_template('/personal_wallet', answer=answer, sell_rate=sell_rate,
                                       sale_proceeds=sale_proceeds, exchange_rate=exchange_rate,
                                       currency_code=currency_code)
            else:
                answer = "The exchange rate cannot be obtained."
                return render_template('/personal_wallet', answer=answer)

    return render_template('/personal_wallet', operation=operation)


if __name__ == '__main__':
    app.run(debug=True)
