pip install -r requirements.txt

pip install ./api ./platform ./simple_visualizer ./block_visualizer

cd graph_explorer

python manage.py makemigrations && python manage.py migrate && python manage.py runserver