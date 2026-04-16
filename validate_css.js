const fs = require('fs');
const css = require('css');

const filePath = './css/styles.css';

try {
  const content = fs.readFileSync(filePath, 'utf8');
  const result = css.parse(content);
  
  if (result.stylesheet.parsingErrors && result.stylesheet.parsingErrors.length > 0) {
    console.log('CSS Parsing Errors Found:');
    result.stylesheet.parsingErrors.forEach((error, index) => {
      console.log('Error ' + (index + 1) + ':', error);
    });
  } else {
    console.log('✓ No CSS syntax errors detected!');
    console.log('Successfully parsed ' + result.stylesheet.rules.length + ' CSS rule(s)');
  }
} catch (error) {
  console.error('Error reading or parsing CSS file:', error.message);
}
