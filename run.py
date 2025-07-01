from app import create_app

# import logging

# Настройка логирования
# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler('api_debug.log'),
#         logging.StreamHandler()
#     ]
# )

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
