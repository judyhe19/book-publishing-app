// src/features/reports/pages/AuthorRoyaltyReportPage.jsx
import React, { useState, useEffect, useMemo } from "react";
import Select from "react-select";
import { useLocation } from "react-router-dom";
import { getAllAuthors } from "../../author/api/authorApi";
import { getAuthorRoyaltyReport } from "../api/reportApi";
import { formatMoney } from "../../../shared/utils/formatUtils";
import { getDefaultQuarterRange } from "../../../shared/utils/quarterUtils";
import {
  PageHeader,
  Button,
  Card,
  CardContent,
  ErrorAlert,
  QuarterRangePicker,
} from "../../../shared/components";
import "./AuthorRoyaltyReportPage.css";



export default function AuthorRoyaltyReportPage() {
  const location = useLocation();
  const initialAuthor = location.state?.author || null;
  const defaults = useMemo(() => getDefaultQuarterRange(), []);

  // Controls state
  const [authors, setAuthors] = useState([]);
  const [selectedAuthor, setSelectedAuthor] = useState(initialAuthor);
  const [startYear, setStartYear] = useState(String(defaults.startYear));
  const [startQuarter, setStartQuarter] = useState(defaults.startQ);
  const [endYear, setEndYear] = useState(String(defaults.endYear));
  const [endQuarter, setEndQuarter] = useState(defaults.endQ);

  // Report state
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Load authors for dropdown
  useEffect(() => {
    getAllAuthors("show_all=true&ordering=name")
      .then((res) => {
        const list = res.results || res;
        setAuthors(
          list.map((a) => ({ value: a.id, label: a.name }))
        );
      })
      .catch(() => {});
  }, []);

  async function handleGenerate() {
    if (!selectedAuthor) return;
    const startYearNum = Number(startYear);
    const endYearNum = Number(endYear);
    if (!startYear || !endYear || startYearNum < 1 || endYearNum < 1) {
      setError("Please enter a valid year.");
      return;
    }
    setLoading(true);
    setError("");
    setReport(null);
    try {
      const data = await getAuthorRoyaltyReport(
        selectedAuthor.value,
        startYearNum,
        startQuarter,
        endYearNum,
        endQuarter
      );
      setReport(data);
    } catch (err) {
      setError(
        err.status === 500
          ? "Too many entries to display, please narrow your search."
          : err.message || "Failed to generate report."
      );
    } finally {
      setLoading(false);
    }
  }

  const generatedDate = new Date().toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="p-6 max-w-full mx-auto">
      {/* ---- Controls (hidden in print) ---- */}
      <div className="royalty-report-controls">
        <PageHeader
          title="Author Royalty Report"
          subtitle="Select an author and quarterly date range to generate a royalty report."
        />

        <Card className="mb-6">
          <CardContent>
            <div className="flex flex-wrap gap-4 items-end">
              <div className="flex-1 min-w-[200px]">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Author
                </label>
                <Select
                  options={authors}
                  value={selectedAuthor}
                  onChange={setSelectedAuthor}
                  placeholder="Select author…"
                  isClearable
                  classNamePrefix="react-select"
                />
              </div>

              <QuarterRangePicker
                startYear={startYear}
                onStartYearChange={setStartYear}
                startQuarter={startQuarter}
                onStartQuarterChange={setStartQuarter}
                endYear={endYear}
                onEndYearChange={setEndYear}
                endQuarter={endQuarter}
                onEndQuarterChange={setEndQuarter}
              />

              <Button
                onClick={handleGenerate}
                disabled={!selectedAuthor || loading}
              >
                {loading ? "Generating…" : "Generate Report"}
              </Button>
            </div>
          </CardContent>
        </Card>

        {error && (
          <ErrorAlert variant="leftBorder" className="mb-6">{error}</ErrorAlert>
        )}
      </div>

      {/* ---- Report (visible in print) ---- */}
      {report && (
        <>
          <Button variant="success" className="print-btn mb-4" onClick={() => {
            const authorName = report.author.name.replace(/\s+/g, "_");
            const startLabel = report.quarters[0]?.label.replace(/\s+/g, "");
            const endLabel = report.quarters[report.quarters.length - 1]?.label.replace(/\s+/g, "");
            const prevTitle = document.title;
            document.title = `Royalty_Report_${authorName}_${startLabel}-${endLabel}`;
            window.print();
            document.title = prevTitle;
          }}>
            🖨️ Print / Save as PDF
          </Button>

          <div className="royalty-report" id="royalty-report">
            {/* Header */}
            <div className="report-header">
              <p className="brand">Hypothetical Publishing</p>
              <h1>Author Royalty Report</h1>
              <p className="report-meta">
                Author: <strong>{report.author.name}</strong>
                &nbsp;&nbsp;|&nbsp;&nbsp;
                Period: {report.quarters[0]?.label} – {report.quarters[report.quarters.length - 1]?.label}
                &nbsp;&nbsp;|&nbsp;&nbsp;
                Generated: {generatedDate}
              </p>
            </div>

            {/* Per-quarter tables */}
            {report.quarters.map((qinfo) => (
              <QuarterTable
                key={qinfo.label}
                label={qinfo.label}
                books={report.books}
                data={report.data}
                totals={report.totals}
                totalsLabel="Subtotal"
              />
            ))}

            {/* All-time section */}
            <QuarterTable
              label="All Time"
              books={report.books}
              data={report.data}
              totals={report.totals}
              totalsLabel="Total"
            />

            {/* All-books summary */}
            <AllBooksTable
              quarters={report.quarters}
              totals={report.totals}
            />
          </div>
        </>
      )}
    </div>
  );
}

/** Renders one quarter (or All Time) as a table section */
function QuarterTable({ label, books, data, totals, totalsLabel = "Subtotal" }) {
  return (
    <div className="quarter-section">
      <h2>{label}</h2>
      <table className="report-table">
        <thead>
          <tr>
            <th style={{ minWidth: "200px" }}>Book</th>
            <th className="num">Qty Sold<br />Print<br />Handsold</th>
            <th className="num">Qty Sold<br />Print<br />Kickstarter</th>
            <th className="num">Qty Sold<br />Print<br />Ingram</th>
            <th className="num">Qty Sold<br />Print<br />Amazon</th>
            <th className="num">Qty Sold<br />eBook<br />Kickstarter</th>
            <th className="num">Qty Sold<br />eBook<br />Amazon</th>
            <th className="num">Qty Sold<br />Print<br />Other</th>
            <th className="num">Qty Sold<br />eBook<br />Other</th>
            <th className="num">Qty Sold<br />Total</th>
            <th className="num">KENP</th>
            <th className="num">Royalty<br />Unpaid</th>
            <th className="num">Royalty<br />Paid</th>
            <th className="num">Royalty<br />Total</th>
          </tr>
        </thead>
        <tbody>
          {books.map((book) => {
            const row = data[book.id]?.[label] || {};
            return (
              <tr key={book.id}>
                <td>
                  {book.series_display && (
                    <span className="series-label">{book.series_display} — </span>
                  )}
                  <span className="book-title">{book.title}</span>
                </td>
                <td className="num">{row.quantity_sold_print_handsold ?? 0}</td>
                <td className="num">{row.quantity_sold_print_kickstarter ?? 0}</td>
                <td className="num">{row.quantity_sold_print_ingram_spark ?? 0}</td>
                <td className="num">{row.quantity_sold_print_amazon ?? 0}</td>
                <td className="num">{row.quantity_sold_ebook_kickstarter ?? 0}</td>
                <td className="num">{row.quantity_sold_ebook_amazon ?? 0}</td>
                <td className="num">{row.quantity_sold_print_other ?? 0}</td>
                <td className="num">{row.quantity_sold_ebook_other ?? 0}</td>
                <td className="num">{row.quantity_sold_total ?? 0}</td>
                <td className="num">{row.kenp ?? 0}</td>
                <td className="num">{formatMoney(row.royalty_unpaid, "$0.00")}</td>
                <td className="num">{formatMoney(row.royalty_paid, "$0.00")}</td>
                <td className="num">{formatMoney(row.royalty_total, "$0.00")}</td>
              </tr>
            );
          })}

          {/* All-books totals row */}
          <tr className="totals-row">
            <td>{totalsLabel}</td>
            <td className="num">{totals[label]?.quantity_sold_print_handsold ?? 0}</td>
            <td className="num">{totals[label]?.quantity_sold_print_kickstarter ?? 0}</td>
            <td className="num">{totals[label]?.quantity_sold_print_ingram_spark ?? 0}</td>
            <td className="num">{totals[label]?.quantity_sold_print_amazon ?? 0}</td>
            <td className="num">{totals[label]?.quantity_sold_ebook_kickstarter ?? 0}</td>
            <td className="num">{totals[label]?.quantity_sold_ebook_amazon ?? 0}</td>
            <td className="num">{totals[label]?.quantity_sold_print_other ?? 0}</td>
            <td className="num">{totals[label]?.quantity_sold_ebook_other ?? 0}</td>
            <td className="num">{totals[label]?.quantity_sold_total ?? 0}</td>
            <td className="num">{totals[label]?.kenp ?? 0}</td>
            <td className="num">{formatMoney(totals[label]?.royalty_unpaid, "$0.00")}</td>
            <td className="num">{formatMoney(totals[label]?.royalty_paid, "$0.00")}</td>
            <td className="num">{formatMoney(totals[label]?.royalty_total, "$0.00")}</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}

/** Renders the All Books summary — one row per quarter plus All Time grand total */
function AllBooksTable({ quarters, totals }) {
  return (
    <div className="quarter-section">
      <h2>All Books</h2>
      <table className="report-table all-books-table">
        <thead>
          <tr>
            <th>Quarter</th>
            <th className="num">Qty Sold<br />Print<br />Handsold</th>
            <th className="num">Qty Sold<br />Print<br />Kickstarter</th>
            <th className="num">Qty Sold<br />Print<br />Ingram</th>
            <th className="num">Qty Sold<br />Print<br />Amazon</th>
            <th className="num">Qty Sold<br />eBook<br />Kickstarter</th>
            <th className="num">Qty Sold<br />eBook<br />Amazon</th>
            <th className="num">Qty Sold<br />Print<br />Other</th>
            <th className="num">Qty Sold<br />eBook<br />Other</th>
            <th className="num">Qty Sold<br />Total</th>
            <th className="num">KENP</th>
            <th className="num">Royalty<br />Unpaid</th>
            <th className="num">Royalty<br />Paid</th>
            <th className="num">Royalty<br />Total</th>
          </tr>
        </thead>
        <tbody>
          {quarters.map((qinfo) => {
            const row = totals[qinfo.label] || {};
            return (
              <tr key={qinfo.label}>
                <td><span className="book-title">{qinfo.label}</span></td>
                <td className="num">{row.quantity_sold_print_handsold ?? 0}</td>
                <td className="num">{row.quantity_sold_print_kickstarter ?? 0}</td>
                <td className="num">{row.quantity_sold_print_ingram_spark ?? 0}</td>
                <td className="num">{row.quantity_sold_print_amazon ?? 0}</td>
                <td className="num">{row.quantity_sold_ebook_kickstarter ?? 0}</td>
                <td className="num">{row.quantity_sold_ebook_amazon ?? 0}</td>
                <td className="num">{row.quantity_sold_print_other ?? 0}</td>
                <td className="num">{row.quantity_sold_ebook_other ?? 0}</td>
                <td className="num">{row.quantity_sold_total ?? 0}</td>
                <td className="num">{row.kenp ?? 0}</td>
                <td className="num">{formatMoney(row.royalty_unpaid, "$0.00")}</td>
                <td className="num">{formatMoney(row.royalty_paid, "$0.00")}</td>
                <td className="num">{formatMoney(row.royalty_total, "$0.00")}</td>
              </tr>
            );
          })}

          {/* Grand total row */}
          <tr className="totals-row">
            <td>Total</td>
            <td className="num">{totals["All Time"]?.quantity_sold_print_handsold ?? 0}</td>
            <td className="num">{totals["All Time"]?.quantity_sold_print_kickstarter ?? 0}</td>
            <td className="num">{totals["All Time"]?.quantity_sold_print_ingram_spark ?? 0}</td>
            <td className="num">{totals["All Time"]?.quantity_sold_print_amazon ?? 0}</td>
            <td className="num">{totals["All Time"]?.quantity_sold_ebook_kickstarter ?? 0}</td>
            <td className="num">{totals["All Time"]?.quantity_sold_ebook_amazon ?? 0}</td>
            <td className="num">{totals["All Time"]?.quantity_sold_print_other ?? 0}</td>
            <td className="num">{totals["All Time"]?.quantity_sold_ebook_other ?? 0}</td>
            <td className="num">{totals["All Time"]?.quantity_sold_total ?? 0}</td>
            <td className="num">{totals["All Time"]?.kenp ?? 0}</td>
            <td className="num">{formatMoney(totals["All Time"]?.royalty_unpaid, "$0.00")}</td>
            <td className="num">{formatMoney(totals["All Time"]?.royalty_paid, "$0.00")}</td>
            <td className="num">{formatMoney(totals["All Time"]?.royalty_total, "$0.00")}</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
