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


# Kupno walut
def buy_currency(currency_code, amount):
    exchange_rate = nbp_data(f'exchangerates/rates/A/{currency_code}/?format=json')
    if exchange_rate:
        buy_rate = exchange_rate['rates'][0]['mid']
        cost = buy_rate * amount
        if cost > account_balance:
            print("Niewystarczające saldo na koncie.")
        else:
            account_balance -= cost
            print("Kupiono {} {} za {:.2f} PLN.".format(amount, currency_code, cost))
    else:
        print("Nie można uzyskać kursu wymiany.")


# Sprzedaż walut
def sell_currency(currency_code, amount):
    exchange_rate = nbp_data(f'exchangerates/rates/A/{currency_code}/?format=json')
    if exchange_rate:
        sell_rate = exchange_rate['rates'][0]['mid']
        sale_proceeds = sell_rate * amount
        account_balance += sale_proceeds
        print("Sprzedano {} {} za {:.2f} PLN.".format(amount, currency_code, sale_proceeds))
    else:
        print("Nie można uzyskać kursu wymiany.")


# Portfel osobisty
def personal_wallet():
    print("Portfel osobisty:")
    for currency in currencies[0]['rates']:
        code = currency['code']
        amount = 0  # Wprowadź ilość waluty w portfelu
        print("{}: {:.2f}".format(code, amount))


while True:
    print("\nWybierz operację:")
    print("1. Dodaj środki do konta")
    print("2. Odbierz środki z konta")
    print("3. Kup walutę")
    print("4. Sprzedaj walutę")
    print("5. Wyświetl saldo konta")
    print("6. Wyjdź")

    choice = input("Wybierz numer operacji: ")

    if choice == '1':
        amount = float(input("Podaj kwotę do dodania: "))
        add_funds(amount)
    elif choice == '2':
        amount = float(input("Podaj kwotę do odebrania: "))
        withdraw_funds(amount)
    elif choice == '3':
        currency_code = input("Podaj kod waluty do zakupu: ")
        amount = float(input("Podaj ilość do zakupu: "))
        buy_currency(currency_code, amount)
    elif choice == '4':
        currency_code = input("Podaj kod waluty do sprzedaży: ")
        amount = float(input("Podaj ilość do sprzedaży: "))
        sell_currency(currency_code, amount)
    elif choice == '5':
        print("Saldo konta: {:.2f} PLN".format(account_balance))
    elif choice == '6':
        break
    else:
        print("Niepoprawny wybór. Wybierz ponownie.")

# Po zakończeniu działania programu możesz zapisać saldo konta do pliku
save_to_file('saldo_konta.json', {"saldo": account_balance})


@app.route('/', methods=['GET', 'POST'])
def home_page():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)

        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")

        return render_template('Home_page.html', current_time=current_time)

        # Obsługa operacji bankowych
        operation = request.form.get('operation')
        if operation == 'add_funds':
            amount = float(request.form.get('amount'))
            # Dodaj środki do konta
            # Tutaj możesz użyć funkcji `add_funds`
        elif operation == 'withdraw_funds':
            amount = float(request.form.get('amount'))
            # Odejmij środki z konta
            # Tutaj możesz użyć funkcji `withdraw_funds`
        elif operation == 'buy_currency':
            currency_code = request.form.get('currency_code')
            amount = float(request.form.get('amount'))
            # Kup walutę
            # Tutaj możesz użyć funkcji `buy_currency`
        elif operation == 'sell_currency':
            currency_code = request.form.get('currency_code')
            amount = float(request.form.get('amount'))
            # Sprzedaj walutę
            # Tutaj możesz użyć funkcji `sell_currency`

        # Pobierz saldo konta
        # Tutaj możesz użyć funkcji do pobrania salda konta

        # Pobierz listę walut
    currencies = nbp_data('exchangerates/tables/A/?format=json')

    return render_template('Home_page.html', account_balance=account_balance, currencies=currencies)


@app.route('/nbp_data', methods=['GET', 'POST'])
def nbp_data(endpoint):
    if request.method == 'POST':
        response = requests.get(api_flask + endpoint)
        if response.status_code == 200:
            return response.json()
        else:
            print("Error while downloading data.")

        return render_template('nbp_data.html', response=response)

    return redirect(request.url)


@app.route('/save_to_file', methods=['GET', 'POST'])
def save_to_file(filename, data):
    with open(filename, mode='w') as file:
        json.dump(data, file, indent=4)

    if request.method == 'POST':

        currencies = nbp_data('exchangerates/tables/A/?format=json')
        if currencies:
            save_to_file('currencies_list.json', currencies)

        transaction_history = nbp_data('transaction_history')
        if transaction_history:
            save_to_file('transaction_history.json', transaction_history)

        return render_template('save_to_file.html', transaction_history=transaction_history,
                               currencies=currencies)

    return redirect(request.url)


# Funkcja do dodawania środków do konta
@app.route('/account_balance_operations.html', methods=['GET', 'POST'])
def account(amount):
    global account_balance
    if request.method == 'POST':
        account_balance += amount
        return "Dodano {:.2f} PLN do konta.".format(amount)

    if amount > account_balance:
        return "Niewystarczające saldo na koncie."
    else:
        account_balance -= amount
        return "Odebrano {:.2f} PLN z konta.".format(amount)


if __name__ == '__main__':
    app.run(debug=True)
