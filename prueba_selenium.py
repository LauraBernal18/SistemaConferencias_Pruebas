from selenium import webdriver

# Abrir Google Chrome
driver = webdriver.Chrome()

# Ingresar a una página de prueba
driver.get("https://www.google.com")

# Mostrar el título de la página
print(driver.title)

# Cerrar el navegador
driver.quit()