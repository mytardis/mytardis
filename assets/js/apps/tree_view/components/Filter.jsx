// Helper functions for filtering
export const defaultMatcher = (filterText, node) => node.name.toLowerCase()
  .indexOf(filterText.toLowerCase()) !== -1;

export const findNode = (node, filter, matcher) => matcher(filter, node) // i match
        || (node.children // or i have decendents and one of them match
            && node.children.length
            && !!node.children.find(child => findNode(child, filter, matcher)));

export const filterTree = (node, filter, matcher = defaultMatcher) => {
  // If im an exact match then all my children get to stay
  if (matcher(filter, node) || !node.children) {
    return node;
  }
  // If not then only keep the ones that match or have matching descendants
  const filtered = node.children
    .filter(child => findNode(child, filter, matcher))
    .map(child => filterTree(child, filter, matcher));
  return Object.assign({}, node, { children: filtered });
};

export const expandFilteredNodes = (node, filter, matcher = defaultMatcher) => {
  let { children } = node;
  if (!children || children.length === 0) {
    return Object.assign({}, node, { toggled: false });
  }
  const childrenWithMatches = node.children.filter(child => findNode(child, filter, matcher));
  const shouldExpand = childrenWithMatches.length > 0;
  // If im going to expand, go through all the matches and see if thier children need to expand
  if (shouldExpand) {
    children = childrenWithMatches.map(child => expandFilteredNodes(child, filter, matcher));
  }
  return Object.assign({}, node, {
    children,
    toggled: shouldExpand,
  });
};

export const findSelectedNode = (node) => {
  let selectedIds = [];
  if (node.selected) {
    selectedIds = [...selectedIds, node.id];
    // selectedIds.push(node.id);
  }
  if (node.children && node.children.length) {
    const selectedNode = node.children.find(child => findSelectedNode(child));
  }
  return selectedIds;
};
export const findSelected = (node, selectedIds) => {
  // if i don't have children and im selected
  if (!node.children && node.selected) {
    selectedIds.push(node.id);
  }
  // if i don't have children and im not selected
  if (!node.children && !node.selected) {
    return [];
  }
  // if i have children, recursively find selected
  if (node.children && node.children.length) {
    const filtered = node.children
      .filter(child => findSelectedNode(child));
    const selected = filtered.map(child => findSelected(child, selectedIds));
    selectedIds = [...selectedIds, ...selected];
  }
  return selectedIds;
};
