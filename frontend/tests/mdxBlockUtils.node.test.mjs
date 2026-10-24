import test from 'node:test';
import assert from 'node:assert/strict';
import { countMdxBlockNodes } from '../lib/mdxBlockUtils.mjs';

test('countMdxBlockNodes counts nested headings, code blocks, and max depth accurately', () => {
  assert.deepStrictEqual(countMdxBlockNodes(null), {
    totalBlocks: 0,
    headingCount: 0,
    codeBlockCount: 0,
    maxDepth: 0
  });

  const tree = {
    type: 'root',
    children: [
      { type: 'heading', depth: 1, children: [{ type: 'text', value: 'Intro' }] },
      {
        type: 'blockquote',
        children: [
          { type: 'paragraph', children: [{ type: 'code', value: 'const x = 1;' }] }
        ]
      }
    ]
  };

  const stats = countMdxBlockNodes(tree);
  assert.strictEqual(stats.totalBlocks, 5);
  assert.strictEqual(stats.headingCount, 1);
  assert.strictEqual(stats.codeBlockCount, 1);
  assert.strictEqual(stats.maxDepth, 3);
});
