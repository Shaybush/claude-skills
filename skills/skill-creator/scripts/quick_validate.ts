#!/usr/bin/env -S npx tsx
/**
 * Quick validation script for skills - minimal version
 */

import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

export interface ValidationResult {
  valid: boolean;
  message: string;
}

export function validateSkill(skillPath: string): ValidationResult {
  // Check SKILL.md exists
  const skillMd = join(skillPath, 'SKILL.md');
  if (!existsSync(skillMd)) {
    return { valid: false, message: 'SKILL.md not found' };
  }

  // Read and validate frontmatter
  const content = readFileSync(skillMd, 'utf-8');
  if (!content.startsWith('---')) {
    return { valid: false, message: 'No YAML frontmatter found' };
  }

  // Extract frontmatter
  const match = content.match(/^---\n([\s\S]*?)\n---/);
  if (!match) {
    return { valid: false, message: 'Invalid frontmatter format' };
  }

  const frontmatter = match[1];

  // Check required fields
  if (!frontmatter.includes('name:')) {
    return { valid: false, message: "Missing 'name' in frontmatter" };
  }
  if (!frontmatter.includes('description:')) {
    return { valid: false, message: "Missing 'description' in frontmatter" };
  }

  // Extract name for validation
  const nameMatch = frontmatter.match(/name:\s*(.+)/);
  if (nameMatch) {
    const name = nameMatch[1].trim();
    // Check naming convention (hyphen-case: lowercase with hyphens)
    if (!/^[a-z0-9-]+$/.test(name)) {
      return {
        valid: false,
        message: `Name '${name}' should be hyphen-case (lowercase letters, digits, and hyphens only)`,
      };
    }
    if (name.startsWith('-') || name.endsWith('-') || name.includes('--')) {
      return {
        valid: false,
        message: `Name '${name}' cannot start/end with hyphen or contain consecutive hyphens`,
      };
    }
  }

  // Extract and validate description
  const descMatch = frontmatter.match(/description:\s*(.+)/);
  if (descMatch) {
    const description = descMatch[1].trim();
    // Check for angle brackets
    if (description.includes('<') || description.includes('>')) {
      return { valid: false, message: 'Description cannot contain angle brackets (< or >)' };
    }
  }

  return { valid: true, message: 'Skill is valid!' };
}

// Run as CLI only when invoked directly
if (process.argv[1] && import.meta.url === `file://${process.argv[1]}`) {
  if (process.argv.length !== 3) {
    console.log('Usage: quick_validate.ts <skill_directory>');
    process.exit(1);
  }

  const { valid, message } = validateSkill(process.argv[2]);
  console.log(message);
  process.exit(valid ? 0 : 1);
}
