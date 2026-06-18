#!/usr/bin/env -S npx tsx
/**
 * Skill Packager - Creates a distributable zip file of a skill folder
 *
 * Usage:
 *     scripts/package_skill.ts <path/to/skill-folder> [output-directory]
 *
 * Example:
 *     scripts/package_skill.ts skills/public/my-skill
 *     scripts/package_skill.ts skills/public/my-skill ./dist
 */

import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, rmSync, statSync } from 'node:fs';
import { basename, dirname, join, resolve } from 'node:path';
import { validateSkill } from './quick_validate.ts';

// ponytail: shell out to system `zip` instead of bundling an archiver dep.
// Add a JS zip lib only if a target env lacks the `zip` binary.
export function packageSkill(skillPathArg: string, outputDir?: string): string | null {
  const skillPath = resolve(skillPathArg);

  // Validate skill folder exists
  if (!existsSync(skillPath)) {
    console.log(`❌ Error: Skill folder not found: ${skillPath}`);
    return null;
  }

  if (!statSync(skillPath).isDirectory()) {
    console.log(`❌ Error: Path is not a directory: ${skillPath}`);
    return null;
  }

  // Validate SKILL.md exists
  const skillMd = join(skillPath, 'SKILL.md');
  if (!existsSync(skillMd)) {
    console.log(`❌ Error: SKILL.md not found in ${skillPath}`);
    return null;
  }

  // Run validation before packaging
  console.log('🔍 Validating skill...');
  const { valid, message } = validateSkill(skillPath);
  if (!valid) {
    console.log(`❌ Validation failed: ${message}`);
    console.log('   Please fix the validation errors before packaging.');
    return null;
  }
  console.log(`✅ ${message}\n`);

  // Determine output location
  const skillName = basename(skillPath);
  let outputPath: string;
  if (outputDir) {
    outputPath = resolve(outputDir);
    mkdirSync(outputPath, { recursive: true });
  } else {
    outputPath = process.cwd();
  }

  const zipFilename = join(outputPath, `${skillName}.zip`);

  // Create the zip file. Run `zip` from the skill's parent so archive entries
  // are prefixed with the skill directory name (matches the Python zipfile layout).
  try {
    if (existsSync(zipFilename)) {
      rmSync(zipFilename);
    }
    execFileSync('zip', ['-r', zipFilename, skillName], {
      cwd: dirname(skillPath),
      stdio: 'inherit',
    });

    console.log(`\n✅ Successfully packaged skill to: ${zipFilename}`);
    return zipFilename;
  } catch (e) {
    console.log(`❌ Error creating zip file: ${(e as Error).message}`);
    return null;
  }
}

function main(): void {
  const args = process.argv.slice(2);
  if (args.length < 1) {
    console.log('Usage: scripts/package_skill.ts <path/to/skill-folder> [output-directory]');
    console.log('\nExample:');
    console.log('  scripts/package_skill.ts skills/public/my-skill');
    console.log('  scripts/package_skill.ts skills/public/my-skill ./dist');
    process.exit(1);
  }

  const skillPath = args[0];
  const outputDir = args[1];

  console.log(`📦 Packaging skill: ${skillPath}`);
  if (outputDir) {
    console.log(`   Output directory: ${outputDir}`);
  }
  console.log();

  const result = packageSkill(skillPath, outputDir);
  process.exit(result ? 0 : 1);
}

if (process.argv[1] && import.meta.url === `file://${process.argv[1]}`) {
  main();
}
