const { chromium } = require('playwright');
(async () => {
    try {
        console.log('Iniciando prueba de Playwright...');
        const browser = await chromium.launch({ headless: true });
        console.log('¡Navegador iniciado exitosamente!');
        const page = await browser.newPage();
        await page.goto('https://www.google.com');
        console.log('Navegación exitosa a Google.com');
        await browser.close();
        console.log('Prueba finalizada sin errores.');
    } catch (err) {
        console.error('Error en la prueba de Playwright:', err);
        process.exit(1);
    }
})();
