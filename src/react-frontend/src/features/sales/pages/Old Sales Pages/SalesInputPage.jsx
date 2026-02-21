import React from 'react';
import { useNavigate } from 'react-router-dom';
import SaleEntryRow from '../../../shared/components/SaleEntryRow';
import { Button } from '../../../shared/components/Button';
import { useSalesInputPage } from '../hooks/useSalesInputPage';

const SalesInputPage = () => {
    const navigate = useNavigate();
    const {
        rows,
        isSubmitting,
        error,
        handleRowChange,
        handleRemoveRow,
        handleSubmit
    } = useSalesInputPage();

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <h1 className="text-2xl font-semibold text-gray-900 mb-6 font-display">Sales Input Tool</h1>

            {error && (
                <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-4 rounded-md">
                    <div className="flex">
                        <div className="ml-3">
                            <p className="text-sm text-red-700 whitespace-pre-wrap">{error}</p>
                        </div>
                    </div>
                </div>
            )}

            <div className="space-y-4">
                {rows.map((row, index) => (
                    <SaleEntryRow
                        key={index}
                        index={index}
                        data={row}
                        onChange={handleRowChange}
                        onRemove={handleRemoveRow}
                        isFirst={index === 0}
                    />
                ))}
            </div>

            <div className="mt-8 flex justify-end gap-4">
                <Button variant="secondary" onClick={() => navigate(-1)}>
                    Cancel
                </Button>
                <Button onClick={handleSubmit} disabled={isSubmitting}>
                    {isSubmitting ? 'Submitting...' : 'Submit All Sales'}
                </Button>
            </div>
        </div>
    );
};

export default SalesInputPage;
