import {readFileSync, writeFileSync} from 'node:fs';
import {dirname, join} from 'node:path';
import {fileURLToPath} from 'node:url';

const ctx = process.argv[2];
const root = join(dirname(fileURLToPath(import.meta.url)), '../..');
const brandDir = join(root, 'whitelabel/brand', ctx);
const brand = JSON.parse(readFileSync(join(brandDir, 'brand.json'), 'utf8'));
const wordmark = readFileSync(join(brandDir, 'wordmark.svg'), 'utf8');

function patch(file, replacements) {
	const path = join(root, file);
	let text = readFileSync(path, 'utf8');
	for (const [pattern, replacement] of replacements) {
		if (!pattern.test(text)) {
			throw new Error(`brand.mjs: ${pattern} not found in ${file}`);
		}
		text = text.replace(pattern, () => replacement);
	}
	writeFileSync(path, text);
}

function escapeHtml(value) {
	return value.replaceAll('&', '&amp;').replaceAll('"', '&quot;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
}

function fontFace({family, file}) {
	const data = readFileSync(join(root, 'whitelabel/fonts', file)).toString('base64');
	return `@font-face{font-family:'${family}';src:url(data:font/woff2;base64,${data}) format('woff2');font-weight:100 900;font-display:swap;}`;
}

const viewBox = wordmark.match(/viewBox="([^"]+)"/)[1];
const paths = [...wordmark.matchAll(/ d="([^"]+)"/g)].map((match) => match[1]);
const name = brand.product_name;
const {body, heading} = brand.fonts;

let css = [body, heading].filter(Boolean).map(fontFace).join('');
if (body) {
	css += `:root,:root.platform-windows:not(.windows-fluxer-sans){--font-sans-primary:'${body.family}';}`;
}
if (heading) {
	css += `h1,h2{font-family:'${heading.family}',var(--font-sans)!important;letter-spacing:${heading.letter_spacing ?? 'normal'}!important;}`;
}
css += '[data-flx="auth.components.auth-brand-panel.host"]{display:none;}';

patch('fluxer_app/src/features/app/config/ProductConstants.ts', [
	[/export const PRODUCT_NAME = '[^']*';/, `export const PRODUCT_NAME = ${JSON.stringify(name)};`],
]);
writeFileSync(join(root, 'fluxer_app/src/media/images/fluxer-wordmark.svg'), wordmark);
patch('packages/desktop_ipc/src/NativeTitlebarShell.ts', [
	[/const NATIVE_TITLEBAR_DEFAULT_PRODUCT_NAME = '[^']*';/, `const NATIVE_TITLEBAR_DEFAULT_PRODUCT_NAME = ${JSON.stringify(name)};`],
	[/const NATIVE_TITLEBAR_WORDMARK_VIEWBOX = '[^']*';/, `const NATIVE_TITLEBAR_WORDMARK_VIEWBOX = ${JSON.stringify(viewBox)};`],
	[
		/const NATIVE_TITLEBAR_WORDMARK_PATHS: ReadonlyArray<string> = \[[\s\S]*?\n\];/,
		`const NATIVE_TITLEBAR_WORDMARK_PATHS: ReadonlyArray<string> = ${JSON.stringify(paths)};`,
	],
	[/<path fill="currentColor" d="\$\{d\}"\/>/, `<path fill="${brand.color}" d="\${d}"/>`],
]);
patch('fluxer_app/index.html', [
	[/<meta name="apple-mobile-web-app-title" content="[^"]*">/, `<meta name="apple-mobile-web-app-title" content="${escapeHtml(name)}">`],
	[/<\/head>/, `<style id="fluxer-instance-theme-color" data-color="${brand.color}"></style>\n</head>`],
	[/<\/body>/, `<style id="fluxer-instance-custom-css">${css}</style>\n</body>`],
]);
console.log(`brand.mjs: ${ctx} applied (${name})`);
