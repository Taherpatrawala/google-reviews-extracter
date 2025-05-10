import React, { useState, useCallback } from "react";
import { Search } from "lucide-react";

interface Review {
  Name: string;
  Stars: string;
  Date: string;
  Review: string;
  Image: string;
}

type ApiResponseData = { reviews: Review[] } | { titles: string[] };

interface ApiErrorResponse {
  Error?: string;
  error?: string;
  message?: string;
}

const ReviewFetcher: React.FC = () => {
  const [query, setQuery] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [data, setData] = useState<ApiResponseData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchReviews = useCallback(
    async (customQuery?: string) => {
      const searchQuery = customQuery || query;
      if (!searchQuery.trim()) {
        setError("Please enter a search query.");
        setData(null);
        return;
      }

      setLoading(true);
      setError(null);
      setData(null);

      const API_URL = "http://127.0.0.1:8000/api/getReviewsOld/?";
      const params = new URLSearchParams({ q: searchQuery.trim() }).toString();

      try {
        const response = await fetch(`${API_URL}${params}`);
        if (!response.ok) {
          const errorData = (await response.json()) as ApiErrorResponse;
          throw {
            response: {
              status: response.status,
              statusText: response.statusText,
              data: errorData,
            },
          };
        }

        const responseData = (await response.json()) as ApiResponseData;
        setData(responseData);
      } catch (err: any) {
        if (err.response) {
          const apiError = err.response.data as ApiErrorResponse;
          if (apiError.Error) {
            setError(`API Error: ${apiError.Error}`);
          } else if (apiError.error || apiError.message) {
            setError(`API Error: ${apiError.error || apiError.message}`);
          } else {
            setError(
              `API Error: ${err.response.status} ${err.response.statusText}`
            );
          }
        } else if (
          err instanceof TypeError &&
          err.message === "Failed to fetch"
        ) {
          setError("Network Error: No response received from server.");
        } else {
          setError(`An unexpected error occurred: ${err.message}`);
        }
        setData(null);
      } finally {
        setLoading(false);
      }
    },
    [query]
  );

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(event.target.value);
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    fetchReviews();
  };

  const renderStars = (starsText: string) => {
    const ratingMatch = starsText.match(/(\d+(\.\d+)?)/);
    if (!ratingMatch) return starsText;

    const rating = parseFloat(ratingMatch[0]);
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;

    return (
      <div className="flex items-center">
        {[...Array(5)].map((_, i) => (
          <span
            key={i}
            className={`text-xl ${
              i < fullStars
                ? "text-yellow-400"
                : i === fullStars && hasHalfStar
                ? "text-yellow-400"
                : "text-gray-300"
            }`}
          >
            {i < fullStars || (i === fullStars && hasHalfStar) ? "★" : "☆"}
          </span>
        ))}
        <span className="ml-2 text-sm font-medium">{starsText}</span>
      </div>
    );
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 bg-lime-50">
      <div className="bg-white rounded-none border-4 border-black p-6 shadow-[8px_8px_0px_0px_rgba(0,0,0)] mb-8">
        <h1 className="text-4xl font-black mb-6 text-center bg-yellow-300 py-2 transform -rotate-1 border-2 border-black">
          LOCATION REVIEW FINDER
        </h1>

        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="relative flex-grow">
            <input
              type="text"
              value={query}
              onChange={handleInputChange}
              placeholder="Enter location or query"
              disabled={loading}
              className="w-full px-4 py-3 border-4 border-black rounded-none text-lg focus:outline-none focus:ring-4 focus:ring-pink-300 focus:border-black"
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  fetchReviews();
                }
              }}
            />
          </div>
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="cursor-pointer bg-blue-500 hover:bg-blue-600 text-white font-bold py-3 px-8 border-4 border-black rounded-none shadow-[5px_5px_0px_0px_rgba(0,0,0)] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0)] transition-all flex items-center justify-center disabled:bg-gray-400 disabled:shadow-none disabled:hover:transform-none"
          >
            {loading ? (
              <svg
                className="animate-spin h-5 w-5 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
            ) : (
              <>
                <Search size={20} className="mr-2" />
                SEARCH
              </>
            )}
          </button>
        </div>

        {error && (
          <div className="bg-red-100 border-4 border-black p-4 mt-4 transform rotate-1 shadow-[5px_5px_0px_0px_rgba(0,0,0)]">
            <p className="text-lg font-bold text-red-600">ERROR!</p>
            <p className="text-red-600">{error}</p>
          </div>
        )}

        {!loading && !error && !data && (
          <div className="bg-blue-100 border-4 border-black p-4 mt-4 transform -rotate-1 shadow-[5px_5px_0px_0px_rgba(0,0,0)]">
            <p className="text-lg font-bold">
              Enter a location or query and click "SEARCH" to fetch reviews!
            </p>
          </div>
        )}
      </div>

      {!loading && !error && data && (
        <div>
          {"reviews" in data && data.reviews.length > 0 && (
            <div className="bg-white border-4 border-black p-6 shadow-[8px_8px_0px_0px_rgba(0,0,0)]">
              <h2 className="text-3xl font-black mb-6 bg-green-300 inline-block py-1 px-4 transform rotate-1 border-2 border-black">
                REVIEWS
              </h2>
              <div className="space-y-6">
                {data.reviews.map((review, index) => (
                  <div
                    key={index}
                    className={`p-4 border-4 border-black shadow-[5px_5px_0px_0px_rgba(0,0,0)] ${
                      index % 3 === 0
                        ? "bg-pink-100 transform -rotate-1"
                        : index % 3 === 1
                        ? "bg-blue-100 transform rotate-1"
                        : "bg-yellow-100"
                    }`}
                  >
                    <div className="flex justify-between flex-col sm:flex-row gap-2">
                      <div className="flex gap-2">
                        <img
                          src={review.Image}
                          alt="Pic"
                          className="w-8 h-8 rounded-full"
                        />
                        <p className="font-bold text-lg">{review.Name}</p>
                      </div>
                      {review.Date !== "NA" && (
                        <div className="flex gap-4 flex-col sm:flex-row">
                          {renderStars(review.Stars)}
                          <p className="text-gray-600 font-mono">
                            {review.Date}
                          </p>
                        </div>
                      )}
                    </div>
                    <p className="mt-2 bg-white p-3 border-2 border-black">
                      {review.Review}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {"titles" in data && data.titles.length > 0 && (
            <div className="bg-white border-4 border-black p-6 shadow-[8px_8px_0px_0px_rgba(0,0,0)]">
              <h2 className="text-3xl font-black mb-4 bg-orange-300 inline-block py-1 px-4 transform rotate-1 border-2 border-black">
                MULTIPLE MATCHES FOUND
              </h2>
              <p className="mb-4 font-bold">Please refine your search query:</p>
              <ul className="space-y-4">
                {data.titles.map((title, index) => (
                  <li
                    key={index}
                    className="relative transform transition-all duration-200"
                  >
                    <button
                      onClick={() => {
                        setQuery(title);
                        fetchReviews(title);
                      }}
                      className={`w-full text-left p-4 border-3 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0)] 
                        hover:shadow-[2px_2px_0px_0px_rgba(0,0,0)] hover:translate-x-1 hover:translate-y-1
                        active:shadow-none active:translate-x-2 active:translate-y-2
                        font-bold transition-all duration-150 ease-in-out cursor-pointer
                        ${
                          index % 4 === 0
                            ? "bg-pink-200"
                            : index % 4 === 1
                            ? "bg-blue-200"
                            : index % 4 === 2
                            ? "bg-green-200"
                            : "bg-yellow-200"
                        }`}
                    >
                      <div className="flex items-center">
                        <div className="mr-2 bg-white w-6 h-6 border-2 border-black flex items-center justify-center rounded-full">
                          {index + 1}
                        </div>
                        <span>{title}</span>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {(("reviews" in data && data.reviews.length === 0) ||
            ("titles" in data && data.titles.length === 0)) && (
            <div className="bg-white border-4 border-black p-6 shadow-[8px_8px_0px_0px_rgba(0,0,0)]">
              <h2 className="text-3xl font-black mb-4 bg-purple-300 inline-block py-1 px-4 transform rotate-1 border-2 border-black">
                NO RESULTS
              </h2>
              <p className="text-lg">
                No results found for your query. Try a different search term.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ReviewFetcher;
