/**
 * Recursively count block-level nodes and maximum nesting depth in an MDX AST or block tree.
 * @param {Array<object>|object|null|undefined} nodes
 * @returns {{ totalBlocks: number, headingCount: number, codeBlockCount: number, maxDepth: number }}
 */
export function countMdxBlockNodes(nodes) {
  let totalBlocks = 0;
  let headingCount = 0;
  let codeBlockCount = 0;
  let maxDepth = 0;

  function visit(list, depth) {
    if (!Array.isArray(list)) return;
    for (const node of list) {
      if (!node || typeof node !== 'object') continue;
      const type = String(node.type || '').toLowerCase();
      if (type) {
        totalBlocks += 1;
        if (depth > maxDepth) maxDepth = depth;
        if (type === 'heading' || /^h[1-6]$/.test(type)) {
          headingCount += 1;
        } else if (type === 'code' || type === 'codeblock' || type === 'pre') {
          codeBlockCount += 1;
        }
      }
      if (Array.isArray(node.children) && node.children.length > 0) {
        visit(node.children, depth + 1);
      }
    }
  }

  const rootList = Array.isArray(nodes)
    ? nodes
    : nodes && Array.isArray(nodes.children)
      ? nodes.children
      : [];
  visit(rootList, 1);

  return { totalBlocks, headingCount, codeBlockCount, maxDepth };
}
