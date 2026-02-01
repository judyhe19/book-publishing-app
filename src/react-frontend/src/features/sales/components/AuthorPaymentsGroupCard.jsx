import { Card, CardContent } from "../../../shared/components/Card";
import { Button } from "../../../shared/components/Button";
import AuthorPaymentsTable from "./AuthorPaymentsTable";

function money(x) {
  const n = Number(x);
  if (Number.isNaN(n)) return "$0.00";
  return n.toLocaleString(undefined, { style: "currency", currency: "USD" });
}

export default function AuthorPaymentsGroupCard({ group, onMarkAllPaid, onGoBook, onGoSale }) {
  const { author, rows, unpaidTotal, unpaidCount } = group;

  return (
    <Card>
      <CardContent>
        <div className="flex justify-between items-start gap-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">{author.name}</h2>
            <p className="text-slate-600 mt-1">
              Unpaid subtotal:{" "}
              <span className="font-semibold text-slate-900">{money(unpaidTotal)}</span>
              {" "}({unpaidCount} unpaid record{unpaidCount === 1 ? "" : "s"})
            </p>
          </div>

          <Button disabled={unpaidCount === 0} onClick={onMarkAllPaid}>
            Mark all unpaid as paid
          </Button>
        </div>

        <div className="mt-4">
          <AuthorPaymentsTable
            rows={rows}
            onGoBook={onGoBook}
            onGoSale={onGoSale}
          />
        </div>
      </CardContent>
    </Card>
  );
}
