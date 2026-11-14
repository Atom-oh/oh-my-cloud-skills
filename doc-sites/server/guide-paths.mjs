export function guideUrl(relative, locale) {
  const segments = relative.split('/');
  if (segments.length > 1 && segments.at(-1) === segments.at(-2)) segments.pop();
  return `${locale === 'en' ? '/en' : ''}/docs/${segments.join('/')}`;
}
