import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import matplotlib.pyplot as plt
import seaborn as sns
from logger import get_logger

class DataQualityAnalyzer:
    """
    Comprehensive data quality analyzer for financial data
    
    Provides:
    - Data completeness analysis
    - Statistical analysis
    - Anomaly detection
    - Data consistency checks
    - Quality scoring
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the data quality analyzer
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = get_logger(__name__, log_file_prefix="data_quality")
        
        # Quality thresholds
        self.completeness_threshold = self.config.get('COMPLETENESS_THRESHOLD', 0.95)
        self.consistency_threshold = self.config.get('CONSISTENCY_THRESHOLD', 0.90)
        self.anomaly_threshold = self.config.get('ANOMALY_THRESHOLD', 3.0)  # Standard deviations
        
    def analyze_data_quality(self, df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """
        Comprehensive data quality analysis
        
        Args:
            df: DataFrame to analyze
            symbol: Symbol for logging purposes
            
        Returns:
            Dict: Comprehensive quality analysis results
        """
        try:
            self.logger.info(f"Starting data quality analysis for {symbol}")
            
            analysis = {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'data_points': len(df),
                'date_range': {
                    'start': df['date'].min() if 'date' in df.columns else None,
                    'end': df['date'].max() if 'date' in df.columns else None
                },
                'completeness': self._analyze_completeness(df),
                'statistics': self._analyze_statistics(df),
                'consistency': self._analyze_consistency(df),
                'anomalies': self._detect_anomalies(df),
                'quality_score': 0.0,
                'recommendations': []
            }
            
            # Calculate overall quality score
            analysis['quality_score'] = self._calculate_quality_score(analysis)
            
            # Generate recommendations
            analysis['recommendations'] = self._generate_recommendations(analysis)
            
            self.logger.info(f"Data quality analysis completed for {symbol}. Score: {analysis['quality_score']:.2f}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in data quality analysis for {symbol}: {e}")
            return {
                'symbol': symbol,
                'error': str(e),
                'quality_score': 0.0
            }
    
    def _analyze_completeness(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze data completeness
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dict: Completeness analysis results
        """
        try:
            # Check for missing values
            missing_data = df.isnull().sum()
            total_cells = len(df) * len(df.columns)
            missing_percentage = (missing_data.sum() / total_cells) * 100
            
            # Check for date gaps
            date_gaps = []
            if 'date' in df.columns:
                df_sorted = df.sort_values('date')
                date_diffs = df_sorted['date'].diff().dt.days
                gaps = date_diffs[date_diffs > 1]
                if not gaps.empty:
                    date_gaps = gaps.tolist()
            
            return {
                'missing_values': missing_data.to_dict(),
                'missing_percentage': missing_percentage,
                'completeness_score': 1 - (missing_percentage / 100),
                'date_gaps': date_gaps,
                'has_date_gaps': len(date_gaps) > 0
            }
            
        except Exception as e:
            self.logger.error(f"Error in completeness analysis: {e}")
            return {'error': str(e)}
    
    def _analyze_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze statistical properties of the data
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dict: Statistical analysis results
        """
        try:
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            available_columns = [col for col in numeric_columns if col in df.columns]
            
            stats = {}
            for col in available_columns:
                if col in df.columns:
                    series = pd.to_numeric(df[col], errors='coerce').dropna()
                    if len(series) > 0:
                        stats[col] = {
                            'count': len(series),
                            'mean': float(series.mean()),
                            'std': float(series.std()),
                            'min': float(series.min()),
                            'max': float(series.max()),
                            'median': float(series.median()),
                            'skewness': float(series.skew()),
                            'kurtosis': float(series.kurtosis())
                        }
            
            # Calculate returns if close price is available
            if 'close' in df.columns:
                close_series = pd.to_numeric(df['close'], errors='coerce').dropna()
                if len(close_series) > 1:
                    returns = close_series.pct_change().dropna()
                    stats['returns'] = {
                        'mean': float(returns.mean()),
                        'std': float(returns.std()),
                        'min': float(returns.min()),
                        'max': float(returns.max()),
                        'skewness': float(returns.skew()),
                        'kurtosis': float(returns.kurtosis())
                    }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error in statistical analysis: {e}")
            return {'error': str(e)}
    
    def _analyze_consistency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze data consistency and logical relationships
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dict: Consistency analysis results
        """
        try:
            consistency_checks = {}
            
            # OHLC consistency checks
            if all(col in df.columns for col in ['open', 'high', 'low', 'close']):
                # High should be >= max of open, close
                high_violations = df['high'] < df[['open', 'close']].max(axis=1)
                # Low should be <= min of open, close
                low_violations = df['low'] > df[['open', 'close']].min(axis=1)
                
                consistency_checks['ohlc_violations'] = {
                    'high_violations': int(high_violations.sum()),
                    'low_violations': int(low_violations.sum()),
                    'total_violations': int(high_violations.sum() + low_violations.sum())
                }
            
            # Volume consistency
            if 'volume' in df.columns:
                negative_volume = (df['volume'] < 0).sum()
                zero_volume = (df['volume'] == 0).sum()
                
                consistency_checks['volume_issues'] = {
                    'negative_volume': int(negative_volume),
                    'zero_volume': int(zero_volume)
                }
            
            # Price consistency
            price_columns = ['open', 'high', 'low', 'close']
            available_price_cols = [col for col in price_columns if col in df.columns]
            
            if available_price_cols:
                negative_prices = {}
                zero_prices = {}
                
                for col in available_price_cols:
                    negative_prices[col] = int((df[col] <= 0).sum())
                    zero_prices[col] = int((df[col] == 0).sum())
                
                consistency_checks['price_issues'] = {
                    'negative_prices': negative_prices,
                    'zero_prices': zero_prices
                }
            
            # Calculate consistency score
            total_checks = len(consistency_checks)
            passed_checks = 0
            
            for check_name, check_data in consistency_checks.items():
                if 'violations' in check_name:
                    if check_data['total_violations'] == 0:
                        passed_checks += 1
                elif 'issues' in check_name:
                    # Fix: properly check if all issues are zero
                    all_zero = True
                    for issue_type, issue_data in check_data.items():
                        if isinstance(issue_data, dict):
                            if any(issue_data.values()):
                                all_zero = False
                                break
                        elif isinstance(issue_data, (int, float)):
                            if issue_data > 0:
                                all_zero = False
                                break
                    if all_zero:
                        passed_checks += 1
            
            consistency_score = passed_checks / total_checks if total_checks > 0 else 1.0
            
            consistency_checks['consistency_score'] = consistency_score
            
            return consistency_checks
            
        except Exception as e:
            self.logger.error(f"Error in consistency analysis: {e}")
            return {'error': str(e)}
    
    def _detect_anomalies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect anomalies in the data
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dict: Anomaly detection results
        """
        try:
            anomalies = {}
            
            # Price anomalies using Z-score
            price_columns = ['open', 'high', 'low', 'close']
            available_price_cols = [col for col in price_columns if col in df.columns]
            
            for col in available_price_cols:
                series = pd.to_numeric(df[col], errors='coerce').dropna()
                if len(series) > 0:
                    z_scores = np.abs((series - series.mean()) / series.std())
                    anomaly_indices = z_scores > self.anomaly_threshold
                    
                    if anomaly_indices.any():
                        anomalies[col] = {
                            'count': int(anomaly_indices.sum()),
                            'indices': df.index[anomaly_indices].tolist(),
                            'values': series[anomaly_indices].tolist(),
                            'z_scores': z_scores[anomaly_indices].tolist()
                        }
            
            # Volume anomalies
            if 'volume' in df.columns:
                volume_series = pd.to_numeric(df['volume'], errors='coerce').dropna()
                if len(volume_series) > 0:
                    z_scores = np.abs((volume_series - volume_series.mean()) / volume_series.std())
                    anomaly_indices = z_scores > self.anomaly_threshold
                    
                    if anomaly_indices.any():
                        anomalies['volume'] = {
                            'count': int(anomaly_indices.sum()),
                            'indices': df.index[anomaly_indices].tolist(),
                            'values': volume_series[anomaly_indices].tolist(),
                            'z_scores': z_scores[anomaly_indices].tolist()
                        }
            
            # Return anomalies
            if 'close' in df.columns:
                close_series = pd.to_numeric(df['close'], errors='coerce').dropna()
                if len(close_series) > 1:
                    returns = close_series.pct_change().dropna()
                    if len(returns) > 0:
                        z_scores = np.abs((returns - returns.mean()) / returns.std())
                        anomaly_indices = z_scores > self.anomaly_threshold
                        
                        if anomaly_indices.any():
                            anomalies['returns'] = {
                                'count': int(anomaly_indices.sum()),
                                'indices': returns.index[anomaly_indices].tolist(),
                                'values': returns[anomaly_indices].tolist(),
                                'z_scores': z_scores[anomaly_indices].tolist()
                            }
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Error in anomaly detection: {e}")
            return {'error': str(e)}
    
    def _calculate_quality_score(self, analysis: Dict[str, Any]) -> float:
        """
        Calculate overall quality score
        
        Args:
            analysis: Complete analysis results
            
        Returns:
            float: Quality score between 0 and 1
        """
        try:
            scores = []
            weights = []
            
            # Completeness score
            if 'completeness' in analysis and 'completeness_score' in analysis['completeness']:
                scores.append(analysis['completeness']['completeness_score'])
                weights.append(0.3)
            
            # Consistency score
            if 'consistency' in analysis and 'consistency_score' in analysis['consistency']:
                scores.append(analysis['consistency']['consistency_score'])
                weights.append(0.4)
            
            # Anomaly score (fewer anomalies = higher score)
            if 'anomalies' in analysis:
                total_anomalies = 0
                for anomaly_data in analysis['anomalies'].values():
                    if isinstance(anomaly_data, dict) and 'indices' in anomaly_data:
                        total_anomalies += len(anomaly_data['indices'])
                
                anomaly_score = max(0, 1 - (total_anomalies / analysis['data_points']))
                scores.append(anomaly_score)
                weights.append(0.3)
            
            # Calculate weighted average
            if scores and weights:
                total_weight = sum(weights)
                weighted_score = sum(score * weight for score, weight in zip(scores, weights)) / total_weight
                return min(1.0, max(0.0, weighted_score))
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating quality score: {e}")
            return 0.0
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Generate recommendations based on analysis results
        
        Args:
            analysis: Complete analysis results
            
        Returns:
            List: List of recommendations
        """
        recommendations = []
        
        try:
            # Completeness recommendations
            if 'completeness' in analysis:
                completeness = analysis['completeness']
                if completeness.get('missing_percentage', 0) > 5:
                    recommendations.append(f"High missing data ({completeness['missing_percentage']:.1f}%). Consider data source with better coverage.")
                
                if completeness.get('has_date_gaps', False):
                    recommendations.append("Date gaps detected. Consider fetching data with different period or source.")
            
            # Consistency recommendations
            if 'consistency' in analysis:
                consistency = analysis['consistency']
                if 'ohlc_violations' in consistency:
                    violations = consistency['ohlc_violations']['total_violations']
                    if violations > 0:
                        recommendations.append(f"OHLC violations detected ({violations}). Data may need cleaning.")
                
                if 'volume_issues' in consistency:
                    volume_issues = consistency['volume_issues']
                    if volume_issues.get('negative_volume', 0) > 0:
                        recommendations.append("Negative volume detected. Data source may have issues.")
            
            # Anomaly recommendations
            if 'anomalies' in analysis:
                total_anomalies = 0
                for anomaly_data in analysis['anomalies'].values():
                    if isinstance(anomaly_data, dict) and 'indices' in anomaly_data:
                        total_anomalies += len(anomaly_data['indices'])
                
                if total_anomalies > analysis['data_points'] * 0.05:  # More than 5% anomalies
                    recommendations.append(f"High number of anomalies detected ({total_anomalies}). Consider outlier detection and removal.")
            
            # Overall quality recommendations
            quality_score = analysis.get('quality_score', 0)
            if quality_score < 0.7:
                recommendations.append("Overall data quality is low. Consider using different data source or period.")
            elif quality_score < 0.9:
                recommendations.append("Data quality is acceptable but could be improved.")
            else:
                recommendations.append("Data quality is excellent.")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return ["Error generating recommendations"]
    
    def generate_quality_report(self, analysis: Dict[str, Any], save_path: Optional[str] = None) -> str:
        """
        Generate a comprehensive quality report
        
        Args:
            analysis: Analysis results
            save_path: Optional path to save the report
            
        Returns:
            str: Formatted report
        """
        try:
            report = []
            report.append("=" * 60)
            report.append(f"DATA QUALITY REPORT - {analysis['symbol']}")
            report.append("=" * 60)
            report.append(f"Generated: {analysis['timestamp']}")
            report.append(f"Data Points: {analysis['data_points']}")
            report.append(f"Quality Score: {analysis['quality_score']:.2f}/1.00")
            report.append("")
            
            # Date range
            if analysis['date_range']['start'] and analysis['date_range']['end']:
                report.append(f"Date Range: {analysis['date_range']['start']} to {analysis['date_range']['end']}")
                report.append("")
            
            # Completeness
            if 'completeness' in analysis:
                report.append("COMPLETENESS ANALYSIS:")
                report.append(f"  Missing Data: {analysis['completeness'].get('missing_percentage', 0):.1f}%")
                report.append(f"  Completeness Score: {analysis['completeness'].get('completeness_score', 0):.2f}")
                if analysis['completeness'].get('has_date_gaps', False):
                    report.append(f"  Date Gaps: {len(analysis['completeness'].get('date_gaps', []))}")
                report.append("")
            
            # Consistency
            if 'consistency' in analysis:
                report.append("CONSISTENCY ANALYSIS:")
                report.append(f"  Consistency Score: {analysis['consistency'].get('consistency_score', 0):.2f}")
                if 'ohlc_violations' in analysis['consistency']:
                    violations = analysis['consistency']['ohlc_violations']
                    report.append(f"  OHLC Violations: {violations['total_violations']}")
                report.append("")
            
            # Anomalies
            if 'anomalies' in analysis:
                report.append("ANOMALY DETECTION:")
                total_anomalies = sum(len(anomaly_data.get('indices', [])) for anomaly_data in analysis['anomalies'].values())
                report.append(f"  Total Anomalies: {total_anomalies}")
                for field, anomaly_data in analysis['anomalies'].items():
                    report.append(f"  {field.capitalize()}: {anomaly_data.get('count', 0)}")
                report.append("")
            
            # Recommendations
            if 'recommendations' in analysis:
                report.append("RECOMMENDATIONS:")
                for i, rec in enumerate(analysis['recommendations'], 1):
                    report.append(f"  {i}. {rec}")
                report.append("")
            
            report.append("=" * 60)
            
            report_text = "\n".join(report)
            
            # Save report if path provided
            if save_path:
                with open(save_path, 'w') as f:
                    f.write(report_text)
                self.logger.info(f"Quality report saved to {save_path}")
            
            return report_text
            
        except Exception as e:
            self.logger.error(f"Error generating quality report: {e}")
            return f"Error generating report: {e}" 