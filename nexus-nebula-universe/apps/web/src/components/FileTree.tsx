"use client";

import { useIDEStore } from "@/lib/ideStore";

function groupPaths(paths: string[]) {
  const root: any = {};
  for (const p of paths) {
    const parts = p.split("/").filter(Boolean);
    let node = root;
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      if (i === parts.length - 1) node[part] = null;
      else {
        node[part] = node[part] || {};
        node = node[part];
      }
    }
  }
  return root;
}

function TreeNode({ name, node, prefix }: { name: string; node: any; prefix: string }) {
  const fullPath = prefix ? `${prefix}/${name}` : name;
  const activePath = useIDEStore((s) => s.activePath);
  const setActivePath = useIDEStore((s) => s.setActivePath);

  const isFile = node === null;
  const isActive = activePath === fullPath;

  if (isFile) {
    return (
      <button
        onClick={() => setActivePath(fullPath)}
        className={[
          "w-full text-left px-2 py-1 rounded text-sm",
          isActive ? "bg-zinc-800 text-white" : "hover:bg-zinc-900 text-zinc-300"
        ].join(" ")}
        title={fullPath}
      >
        {name}
      </button>
    );
  }

  const entries = Object.entries(node).sort(([a, av], [b, bv]) => {
    const aIsFile = av === null;
    const bIsFile = bv === null;
    if (aIsFile !== bIsFile) return aIsFile ? 1 : -1;
    return a.localeCompare(b);
  });

  return (
    <div className="mt-1">
      <div className="px-2 py-1 text-xs font-semibold text-zinc-400">{name}</div>
      <div className="pl-2 border-l border-zinc-800 ml-2">
        {entries.map(([childName, childNode]) => (
          <TreeNode key={childName} name={childName} node={childNode} prefix={fullPath} />
        ))}
      </div>
    </div>
  );
}

export function FileTree() {
  const files = useIDEStore((s) => s.files);
  const paths = Object.keys(files).sort();
  const tree = groupPaths(paths);

  return (
    <div className="h-full overflow-auto p-2">
      <div className="text-xs text-zinc-500 px-2 pb-2">Files</div>
      {Object.entries(tree).map(([name, node]) => (
        <TreeNode key={name} name={name} node={node} prefix="" />
      ))}
    </div>
  );
}
