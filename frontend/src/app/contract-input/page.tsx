"use client";

import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { FormSectionCard } from '@/components/ui/FormSectionCard';
import { SegmentedControl } from '@/components/ui/SegmentedControl';
import { TextInput } from '@/components/ui/TextInput';
import Link from 'next/link';

// --- Icons (SVG) ---
const IconEnvironment = () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6 text-primary-500">
        <path d="M12 2a10 10 0 1 0 10 10 4 4 0 0 1-5-5 4 4 0 0 1-5-5" />
        <path d="M8.5 8.5v.01" />
        <path d="M16 16v.01" />
        <path d="M12 12v.01" />
    </svg>
);
const IconHome = () => <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><polyline points="9 22 9 12 15 12 15 22" /></svg>;
const IconFile = () => <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" /><polyline points="14 2 14 8 20 8" /></svg>;
const IconCheck = () => <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>;

export default function ContractInputPage() {
    // State
    const [contractType, setContractType] = useState('national'); // national, local, internal
    const [isJoint, setIsJoint] = useState('no');
    const [amount, setAmount] = useState('');
    const [period, setPeriod] = useState('');
    const [errors, setErrors] = useState<{ [key: string]: string }>({});

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        const newErrors: any = {};
        if (!amount) newErrors.amount = "사업금액을 입력해주세요.";
        if (!period) newErrors.period = "납품기간을 입력해주세요.";

        setErrors(newErrors);

        if (Object.keys(newErrors).length === 0) {
            alert("검증 성공! 저장되었습니다.");
        }
    };

    return (
        <div className="min-h-screen bg-neutral-50 flex font-sans">

            {/* Sidebar */}
            <aside className="w-64 bg-white border-r border-neutral-200 hidden lg:flex flex-col fixed h-full z-10">
                <div className="p-6 flex items-center gap-3 border-b border-neutral-100">
                    <div className="w-10 h-10 bg-primary-50 rounded-xl flex items-center justify-center">
                        <IconEnvironment />
                    </div>
                    <div>
                        <h1 className="text-lg font-bold text-neutral-900 tracking-tight">K-eco 업무포털</h1>
                        <p className="text-xs text-neutral-500 font-medium tracking-wide">SMART SYSTEM</p>
                    </div>
                </div>

                <nav className="p-4 space-y-1 flex-1 overflow-y-auto">
                    <div className="px-4 py-2 text-xs font-bold text-neutral-400 uppercase tracking-wider">메인 메뉴</div>
                    <Link href="#" className="flex items-center gap-3 px-4 py-3 text-neutral-600 hover:bg-neutral-50 rounded-xl transition-colors font-medium">
                        <IconHome /> 대시보드
                    </Link>
                    <Link href="#" className="flex items-center gap-3 px-4 py-3 bg-primary-50 text-primary-700 rounded-xl font-bold transition-colors shadow-sm ring-1 ring-primary-100">
                        <IconFile /> 계약 등록 관리
                    </Link>
                    <Link href="#" className="flex items-center gap-3 px-4 py-3 text-neutral-600 hover:bg-neutral-50 rounded-xl transition-colors font-medium">
                        <IconCheck /> 심사/승인
                    </Link>
                </nav>

                <div className="p-4 border-t border-neutral-100">
                    <div className="bg-sky-50 p-4 rounded-2xl">
                        <p className="text-xs font-semibold text-sky-800 mb-1">시스템 공지</p>
                        <p className="text-xs text-sky-600 leading-relaxed">
                            2025년도 계약법 개정안이 반영되었습니다. (v2.1)
                        </p>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 lg:ml-64 p-8 max-w-7xl mx-auto w-full">
                {/* Header */}
                <header className="flex justify-between items-center mb-8">
                    <div>
                        <h2 className="text-2xl font-bold text-neutral-900">신규 계약 등록</h2>
                        <p className="text-neutral-500 text-sm mt-1">전자조달시스템 연동을 위한 기초 정보를 입력합니다.</p>
                    </div>
                    <div className="flex gap-3">
                        <Button variant="ghost">취소</Button>
                        <Button variant="secondary" onClick={handleSubmit}>임시저장</Button>
                        <Button onClick={handleSubmit}>제출하기</Button>
                    </div>
                </header>

                {/* Form Grid */}
                <form onSubmit={handleSubmit} className="space-y-6">

                    {/* Section 1: 기본 계약 정보 */}
                    <FormSectionCard
                        title="법적 근거 및 유형"
                        description="해당 계약이 따르는 법령 기준을 선택해주세요."
                    >
                        <div className="col-span-full">
                            <SegmentedControl
                                label="적용 법령 기준"
                                type="tabs"
                                value={contractType}
                                onChange={setContractType}
                                options={[
                                    { label: "국가계약법 적용", value: "national" },
                                    { label: "지방계약법 적용", value: "local" },
                                    { label: "공단 자체 기준", value: "internal" },
                                ]}
                            />
                        </div>

                        <div className="col-span-1">
                            <SegmentedControl
                                label="공동계약 허용 여부"
                                type="pills"
                                value={isJoint}
                                onChange={setIsJoint}
                                options={[
                                    { label: "허용 (공동수급)", value: "yes" },
                                    { label: "불허 (단독계약)", value: "no" },
                                ]}
                            />
                            <p className="text-xs text-neutral-400 mt-2 ml-1">
                                * 공동수급체 구성을 허용할 경우 시스템 분담율 설정이 필요합니다.
                            </p>
                        </div>
                    </FormSectionCard>

                    {/* Section 2: 예산 및 기간 */}
                    <FormSectionCard
                        title="예산 및 기간 정보"
                        description="정확한 사업 금액과 납품 기한을 입력하세요."
                    >
                        <TextInput
                            label="추정 가격 (VAT 별도)"
                            placeholder="예: 50,000,000"
                            suffix="원"
                            required
                            tooltip="부가세가 제외된 순수 추정 가격을 입력하세요."
                            error={errors.amount}
                            value={amount}
                            onChange={(e) => setAmount(e.target.value)}
                        />

                        <TextInput
                            label="기초 금액 (VAT 포함)"
                            placeholder="자동 계산됩니다"
                            suffix="원"
                            readOnly
                            className="bg-neutral-50"
                        />

                        <TextInput
                            label="납품/용역 기한"
                            placeholder="착수일로부터"
                            suffix="일간"
                            required
                            error={errors.period}
                            value={period}
                            onChange={(e) => setPeriod(e.target.value)}
                        />

                        <div className="flex flex-col gap-1.5">
                            <label className="text-sm font-semibold text-neutral-700">과업 지역</label>
                            <select className="flex h-11 w-full rounded-xl border border-neutral-300 bg-white px-4 py-2 text-sm text-neutral-900 focus-visible:border-primary-500 focus-visible:ring-2 focus-visible:ring-primary-100 outline-none">
                                <option>전국 (대한민국)</option>
                                <option>서울특별시</option>
                                <option>인천/경기</option>
                            </select>
                        </div>
                    </FormSectionCard>

                </form>
            </main>
        </div>
    );
}
