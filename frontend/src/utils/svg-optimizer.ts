/**
 * SVG optimization utilities for better performance
 */

export interface SVGOptimizationOptions {
  removeComments?: boolean;
  removeMetadata?: boolean;
  removeUnusedNS?: boolean;
  removeEditorsNSData?: boolean;
  removeEmptyAttrs?: boolean;
  removeHiddenElems?: boolean;
  removeEmptyText?: boolean;
  removeEmptyContainers?: boolean;
  minifyStyles?: boolean;
  convertStyleToAttrs?: boolean;
}

/**
 * Basic SVG optimization for inline SVGs
 * For production, consider using SVGO or similar tools in the build process
 */
export function optimizeSVG(svgString: string, options: SVGOptimizationOptions = {}): string {
  const {
    removeComments = true,
    removeMetadata = true,
    removeUnusedNS = true,
    removeEditorsNSData = true,
    removeEmptyAttrs = true,
    removeHiddenElems = true,
    removeEmptyText = true,
    minifyStyles = true,
    convertStyleToAttrs = true,
  } = options;

  let optimized = svgString;

  // Remove XML comments
  if (removeComments) {
    optimized = optimized.replace(/<!--[\s\S]*?-->/g, '');
  }

  // Remove metadata elements
  if (removeMetadata) {
    optimized = optimized.replace(/<metadata[\s\S]*?<\/metadata>/gi, '');
    optimized = optimized.replace(/<title[\s\S]*?<\/title>/gi, '');
    optimized = optimized.replace(/<desc[\s\S]*?<\/desc>/gi, '');
  }

  // Remove unused namespaces (basic)
  if (removeUnusedNS) {
    optimized = optimized.replace(/xmlns:[a-z]+="[^"]*"/gi, (match) => {
      const prefix = match.match(/xmlns:([a-z]+)=/)?.[1];
      if (prefix && !optimized.includes(`${prefix}:`)) {
        return '';
      }
      return match;
    });
  }

  // Remove editor namespace data
  if (removeEditorsNSData) {
    optimized = optimized.replace(/\s*(inkscape|sodipodi|adobe-illustrator):[^=]*="[^"]*"/gi, '');
  }

  // Remove empty attributes
  if (removeEmptyAttrs) {
    optimized = optimized.replace(/\s+[a-zA-Z-]+=""/g, '');
  }

  // Remove hidden elements
  if (removeHiddenElems) {
    optimized = optimized.replace(/<[^>]*\s+display\s*=\s*["']none["'][^>]*>[\s\S]*?<\/[^>]+>/gi, '');
    optimized = optimized.replace(/<[^>]*\s+visibility\s*=\s*["']hidden["'][^>]*>[\s\S]*?<\/[^>]+>/gi, '');
  }

  // Remove empty text nodes
  if (removeEmptyText) {
    optimized = optimized.replace(/>\s+</g, '><');
  }

  // Basic style minification
  if (minifyStyles) {
    optimized = optimized.replace(/style="([^"]*)"/g, (match, styles) => {
      const minified = styles
        .replace(/\s*;\s*/g, ';')
        .replace(/\s*:\s*/g, ':')
        .replace(/;\s*$/, '');
      return `style="${minified}"`;
    });
  }

  // Convert basic style attributes to presentation attributes
  if (convertStyleToAttrs) {
    optimized = optimized.replace(/style="([^"]*)"/g, (match, styles) => {
      const styleProps = styles.split(';').filter(Boolean);
      const attrs: string[] = [];
      
      styleProps.forEach((prop: string) => {
        const [key, value] = prop.split(':').map((s: string) => s.trim());
        if (key && value) {
          // Convert common CSS properties to SVG attributes
          const attrMap: Record<string, string> = {
            'fill': 'fill',
            'stroke': 'stroke',
            'stroke-width': 'stroke-width',
            'opacity': 'opacity',
            'fill-opacity': 'fill-opacity',
            'stroke-opacity': 'stroke-opacity',
          };
          
          if (attrMap[key]) {
            attrs.push(`${attrMap[key]}="${value}"`);
          }
        }
      });
      
      return attrs.length > 0 ? attrs.join(' ') : '';
    });
  }

  // Clean up multiple spaces
  optimized = optimized.replace(/\s+/g, ' ').trim();

  return optimized;
}

/**
 * Create an optimized SVG component for React
 */
export function createOptimizedSVGComponent(
  svgString: string, 
  componentName: string,
  options?: SVGOptimizationOptions
): string {
  const optimizedSVG = optimizeSVG(svgString, options);
  
  // Extract viewBox and other root attributes
  const viewBoxMatch = optimizedSVG.match(/viewBox="([^"]*)"/);
  const viewBox = viewBoxMatch ? viewBoxMatch[1] : '0 0 24 24';
  
  // Extract the inner content
  const innerContent = optimizedSVG.replace(/<svg[^>]*>/, '').replace(/<\/svg>$/, '');
  
  return `
import React from 'react';

interface ${componentName}Props {
  size?: number | string;
  className?: string;
  color?: string;
}

export const ${componentName}: React.FC<${componentName}Props> = ({ 
  size = 24, 
  className = '', 
  color = 'currentColor' 
}) => (
  <svg
    width={size}
    height={size}
    viewBox="${viewBox}"
    fill={color}
    className={className}
    xmlns="http://www.w3.org/2000/svg"
  >
    ${innerContent}
  </svg>
);

export default ${componentName};
`.trim();
}

/**
 * Preload SVG for better performance
 */
export function preloadSVG(url: string): Promise<string> {
  return fetch(url)
    .then(response => response.text())
    .then(svgText => optimizeSVG(svgText));
}
