import React from "react";

export function Input(props) {
  return (
    <input
      {...props}
      className={[
        "w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-slate-900",
        "placeholder:text-slate-400",
        "focus:outline-none focus:ring-2 focus:ring-slate-900/10 focus:border-slate-300",
        props.className || "",
      ].join(" ")}
    />
  );
}