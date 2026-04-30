from flask import Flask, request, render_template

app = Flask(__name__, template_folder = 'templates')

@app.route('/')
@app.route('/home')
def home():
    return render_template('dashboard.html', methods=['POST'])

@app.route('/notes')
def notes():
    return render_template('notes.html', methods=['POST'])

if __name__ == '__main__':
    app.run(debug=True)