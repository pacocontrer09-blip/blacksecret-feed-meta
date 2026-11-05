# Feed de productos de blacksecret.mx para Meta

GitHub Actions corre `generar_feed.py` una vez al dia (3:00 am MX), lee la lista publica de productos de la tienda y actualiza `feed.csv`.
Meta (catalogo "Productos para blacksecret.mx", 925970951517526) lee ese archivo como fuente programada.

Correr a mano: pestaña Actions > "Actualizar feed de Meta" > Run workflow.
