import requests
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config["SECRET_KEY"] = "SECRET_KEY"
api_flask = 'http://api.nbp.pl/'

account_balance = float(0)
currency_list = []
operation_history = []
register_users = []

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


@app.route('/login_user', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = Users.query.filter_by(username=username).first()
        print(user)

        if user and user.password == password:
            login_user(user)
            return redirect(url_for('home_page'))
        else:
            flash('A user with this name already exists.', 'error')

        return render_template('login_user.html', user=user, username=username, password=password)

    return render_template('login_user.html')


@app.route('/logout_user')
@login_required
def logout():
    logout_user()
    answer_logout = "User logout"
    flash(answer_logout)
    return redirect(url_for('home_page'))


@app.route('/register_user', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = Users.query.filter_by(username=username).first()

        if not user:
            user = Users(username=username, password=password)
            db.session.add(user)
            db.session.commit()
            flash('Succesfully register user!', 'success')
            return redirect(url_for('login'))
        else:
            flash('A user with this name already exists. Try to login in.', 'error')
            return redirect(url_for('login'))

    return render_template('register_user.html')


@app.route('/', methods=['GET', 'POST'])
def home_page():
    today_daytime = datetime.now()
    today = today_daytime.date()
    hour = today_daytime.hour
    minutes = today_daytime.minute
    seconds = today_daytime.second
    today_time = today_daytime.strftime('%Y-%m-%d %H:%M:%S')

    if request.method == 'POST':
        currencies = request.form['currencies']

        try:
            if currencies.lower() == 'table a':
                with open('currencies_first_list.json', mode='r') as currencies_a:
                    currencies_a = json.load(currencies_a)
                    rates_a = currencies_a[0]['rates']
                    for rate in rates_a:
                        currency = rate['currency']
                        code = rate['code']
                        mid = rate['mid']

                return render_template('Home_page.html', currencies_a=currencies_a, currency=currency, code=code,
                                       mid=mid, rates_a=rates_a)

            elif currencies.lower() == 'table b':
                with open('currencies_second_list.json', mode='r') as currencies_b:
                    currencies_b = json.load(currencies_b)
                    rates_b = currencies_b[0]['rates']
                    for rate in rates_b:
                        currency = rate['currency']
                        code = rate['code']
                        mid = rate['mid']

                return render_template('Home_page.html', currencies_b=currencies_b, currency=currency, code=code,
                                       mid=mid, rates_b=rates_b)

            elif currencies.lower() == 'table c':
                with open('currencies_third_list.json', mode='r') as file:
                    currencies_c = json.load(file)
                    rates_c = currencies_c[0]['rates']
                    for rate in rates_c:
                        currency = rate['currency']
                        code = rate['code']
                        mid = rate['bid']

                return render_template('Home_page.html', currencies_c=currencies_c, currency=currency, code=code,
                                       mid=mid, rates_c=rates_c)

        except FileNotFoundError:
            file_not_found = ("JSON file does not exist. Check the file name.")
            return render_template('Home_page.html', file_not_found=file_not_found)

        except json.JSONDecodeError as error:
            json_decode_error = ("JSON decoding error: ", error)
            return render_template('Home_page.html', json_decode_error=json_decode_error, error=error)

        except Exception as error:
            exception_error = ("A different error occurred: ", error)
            return render_template('Home_page.html', error=error, exception_error=exception_error)

        return render_template('Home_page.html', currencies=currencies)

    return render_template('Home_page.html', account_balance=account_balance, today=today, hour=hour, minutes=minutes,
                           seconds=seconds, today_time=today_time)


@app.route('/nbp_data', methods=['GET', 'POST'])
def nbp_data():
    if request.method == 'GET':
        try:
            response_a = requests.get('http://api.nbp.pl/api/exchangerates/tables/A/')
            response_b = requests.get('http://api.nbp.pl/api/exchangerates/tables/B/')
            response_c = requests.get('http://api.nbp.pl/api/exchangerates/tables/C/')
            if response_a.status_code == 200:
                currencies_a = response_a.json()
                if currencies_a:
                    save_table_first('currencies_first_list.json', currencies_a)

            if response_b.status_code == 200:
                currencies_b = response_b.json()
                if currencies_b:
                    save_table_second('currencies_second_list.json', currencies_b)

            if response_c.status_code == 200:
                currencies_c = response_c.json()
                if currencies_c:
                    save_table_third('currencies_third_list.json', currencies_c)

        except Exception as error_message:
            error_message = "Error while downloading data for table.", error_message
            flash(str(error_message))

        flash("You correctly get NBP data")
        return redirect(url_for('home_page'))

    return redirect(url_for('home_page'))


def save_table_first(filename, currencies_a):
    with open(filename, mode='w') as file:
        json.dump(currencies_a, file, indent=4)


def save_table_second(filename, currencies_b):
    with open(filename, mode='w') as file:
        json.dump(currencies_b, file, indent=4)


def save_table_third(filename, currencies_c):
    with open(filename, mode='w') as file:
        json.dump(currencies_c, file, indent=4)


def account_save(filename, data_save):
    with open(filename) as file:
        json_data = json.load(file)
    json_data.append(data_save)
    with open(filename, mode='w') as file:
        json.dump(json_data, file, indent=4)


def history(filename, history):
    with open(filename) as file:
        json_data = json.load(file)
    json_data.append(history)
    with open(filename, mode='w') as file:
        json.dump(json_data, file, indent=4)


def bought_currency(filename, wallet):
    with open(filename) as file:
        json_data = json.load(file)
    json_data.append(wallet)
    with open(filename, mode='w') as file:
        json.dump(json_data, file, indent=4)


@app.route('/account_balance_operations', methods=['GET', 'POST'])
def account():
    global account_balance
    if request.method == 'POST':
        operation_add = request.form.get('add')
        operation_substract = request.form.get('substract')
        if operation_add == 'add':
            amount = float(request.form['add_amount'])
            account_balance += amount
            operation_history = f"Added {amount}"
            flash(f"Added {amount}")
            data_save = \
                {
                    "balance": account_balance,
                    "operation_history": operation_history
                }
            account_save('balance_account.json', data_save)
            return render_template('account_balance_operations.html', account=account, account_balance=account_balance,
                                   amount=amount)

        if operation_substract == 'substract':
            amount = float(request.form['substract_amount'])
            if amount > account_balance:
                flash(f"Lack of sufficient resources to receive {amount}")
            else:
                account_balance -= amount
                flash(f"Substract {amount}")
                operation_history = (f"Substract {amount}")
                data_save = \
                    {
                        "balance": account_balance,
                        "operation_history": operation_history
                    }
                account_save('balance_account.json', data_save)
                return render_template('account_balance_operations.html', account=account,
                                       account_balance=account_balance, amount=amount)

        return render_template('account_balance_operations.html', operation_add=operation_add,
                               operation_substract=operation_substract, account_balance=account_balance)

    return render_template('account_balance_operations.html', account_balance=account_balance)


@app.route('/personal_wallet', methods=['GET', 'POST'])
def bank_wallet():
    global account_balance
    if request.method == 'POST':
        operation_buy = request.form.get('operation_buy')
        operation_sell = request.form.get('operation_sell')
        if operation_buy == 'operation_buy':
            currency_code_buy = request.form.get('currency_code')
            type_of_table_buy = request.form.get('type_table')
            amount = float(request.form.get('buy_amount'))
            exchange_rate = requests.get(
                f'http://api.nbp.pl/api/exchangerates/rates/{type_of_table_buy}/{currency_code_buy}/?format=json')
            if exchange_rate.status_code == 200:
                for_bank_wallet = exchange_rate.json()
                rates = for_bank_wallet['rates'][0]['mid']
                if rates:
                    buy_currency = rates * amount
                    if buy_currency > account_balance:
                        answer = "Insufficient balance in the account."
                        flash(answer)
                        return render_template('Personal_wallet.html', amount=amount, rates=rates,
                                               buy_currency=buy_currency, exchange_rate=exchange_rate,
                                               currency_code_buy=currency_code_buy, account_balance=account_balance)
                    else:
                        account_balance -= buy_currency
                        answer = "Bought {} {} for {:.2f} in PLN.".format(amount, currency_code_buy, buy_currency)
                        buy_history = \
                            {
                                "bought amount": amount,
                                "bought currency": currency_code_buy,
                                "bought for": 'mid'
                            }
                        history('transaction_history.json', buy_history)
                        bought_currency('operation_buy.json', buy_history)
                        flash(answer)
                        return render_template('Personal_wallet.html', amount=amount, account_balance=account_balance,
                                               currency_code_buy=currency_code_buy, buy_currency=buy_currency)
                else:
                    answer = "The exchange rate cannot be obtained."
                    flash(answer)
                    return render_template('Personal_wallet.html')

        elif operation_sell == 'operation_sell':
            sell_currency_code = request.form.get('sell_currency_code')
            sell_type_of_table = request.form.get('sell_type_table')
            amount = float(request.form.get('sale_amount'))
            exchange_rate = requests.get(
                f'http://api.nbp.pl/api/exchangerates/rates/{sell_type_of_table}/{sell_currency_code}/?format=json')
            if exchange_rate.status_code == 200:
                for_bank_wallet = exchange_rate.json()
                rates = for_bank_wallet.get('rates', [])[0].get('mid', None)
                with open('operation_buy.json', mode='r+') as file:
                    file_content = file.read()
                if rates and sell_currency_code in file_content:
                    sell_currency = rates * amount
                    account_balance += sell_currency
                    answer = "Sold {} {} for {:.2f} in PLN.".format(amount, sell_currency_code, sell_currency)
                    sell_history = \
                        {
                            "sold amount": amount,
                            "sold currency": sell_currency_code,
                            "sold for": 'mid'
                        }
                    history('transaction_history.json', sell_history)
                    flash(answer)
                    return render_template('Personal_wallet.html', sell_currency=sell_currency,
                                           account_balance=account_balance,exchange_rate=exchange_rate,
                                           sell_currency_code=sell_currency_code, operation_buy=operation_buy,
                                           operation_sell=operation_sell, file_content=file_content)
                else:
                    answer = "Currency is not in Your wallet"
                    flash(answer)
            else:
                answer = "The exchange rate cannot be obtained."
                flash(answer)
                return render_template('Personal_wallet.html', operation_buy=operation_buy,
                                       operation_sell=operation_sell, account_balance=account_balance)

        return render_template('Personal_wallet.html', operation_buy=operation_buy, operation_sell=operation_sell,
                               account_balance=account_balance)

    return render_template('Personal_wallet.html', account_balance=account_balance)


@app.route('/history', methods=['GET', 'POST'])
def history_page():
    if request.method == 'GET':
        with open('transaction_history.json', mode='r') as json_file:
            for_history = json.load(json_file)

    return render_template('Transaction_history.html', for_history=for_history)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
