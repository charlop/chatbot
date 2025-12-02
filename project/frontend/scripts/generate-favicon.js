#!/usr/bin/env node

/**
 * Generate favicon files for the Contract Review application
 * Uses the primary purple color (#8b5cf6) and "CR" branding
 */

const fs = require('fs');
const path = require('path');
const sharp = require('sharp');

// SVG favicon with cAI branding (Contract Advisor)
const svgContent = `<svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
  <!-- Background with rounded corners -->
  <rect width="32" height="32" rx="6" fill="#8b5cf6"/>

  <!-- cAI Text (lowercase 'c' + uppercase 'AI') -->
  <text x="16" y="22" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="white" text-anchor="middle">cAI</text>
</svg>`;

async function generateFavicons() {
  try {
    // Create public directory if it doesn't exist
    const publicDir = path.join(__dirname, '..', 'public');
    if (!fs.existsSync(publicDir)) {
      fs.mkdirSync(publicDir, { recursive: true });
    }

    // Write SVG file
    const svgPath = path.join(publicDir, 'favicon.svg');
    fs.writeFileSync(svgPath, svgContent);
    console.log('✓ Created favicon.svg');

    // Generate PNG at different sizes
    const sizes = [16, 32, 48, 64];
    const pngBuffers = [];

    for (const size of sizes) {
      const buffer = await sharp(Buffer.from(svgContent))
        .resize(size, size)
        .png()
        .toBuffer();

      pngBuffers.push(buffer);

      // Also save individual PNG files
      const pngPath = path.join(publicDir, `favicon-${size}x${size}.png`);
      fs.writeFileSync(pngPath, buffer);
      console.log(`✓ Created favicon-${size}x${size}.png`);
    }

    // For favicon.ico, we'll use the 32x32 PNG as the main icon
    // ICO format is complex, so we'll just use a PNG renamed as ICO for simplicity
    // Modern browsers handle this well
    const icoPath = path.join(publicDir, 'favicon.ico');
    fs.writeFileSync(icoPath, pngBuffers[1]); // 32x32 PNG
    console.log('✓ Created favicon.ico (32x32)');

    console.log('\nFavicon files generated successfully!');
    console.log('\nGenerated files:');
    console.log('  - public/favicon.svg (for modern browsers)');
    console.log('  - public/favicon.ico (for legacy browsers)');
    console.log('  - public/favicon-16x16.png');
    console.log('  - public/favicon-32x32.png');
    console.log('  - public/favicon-48x48.png');
    console.log('  - public/favicon-64x64.png');
    console.log('\nNext.js will automatically use these files.');

  } catch (error) {
    console.error('Error generating favicons:', error);
    process.exit(1);
  }
}

generateFavicons();
