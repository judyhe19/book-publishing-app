// src/shared/components/Input.jsx
import React from "react";

export function Input(props) {
  return (
    <input
      {...props}
      onWheel={
        props.type === "number"
          ? (e) => e.currentTarget.blur()
          : props.onWheel
      }
      className={[
        "w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-slate-900",
        "placeholder:text-slate-400",
        "focus:outline-none focus:ring-2 focus:ring-slate-900/10 focus:border-slate-300",
        props.type === "number"
          ? "[appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
          : "",
        props.className || "",
      ].join(" ")}
    />
  );
}

export default Input;
