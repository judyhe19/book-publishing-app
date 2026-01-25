export function errorMessage(err) {
  if (!err) return "Something went wrong";
  if (typeof err === "string") return err;
  return err.message || "Something went wrong";
}