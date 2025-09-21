pip install -r requirements.txt

cd graph_explorer

python manage.py makemigrations && python manage.py migrate && python manage.py runserver